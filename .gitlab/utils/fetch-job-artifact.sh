#!/bin/bash
set -euo pipefail

usage() {
    echo "Usage: $0 --ref <ref> --job-name <job_name> --artifact-path <path> --output-path <path> [--exclude-pipeline-id <id>] [--status-output-path <path>] [--directory] [--optional]" >&2
}

ref=""
job_name=""
artifact_path=""
output_path=""
exclude_pipeline_id=""
status_output_path=""
directory=false
optional=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ref) ref=$2; shift 2 ;;
        --job-name) job_name=$2; shift 2 ;;
        --artifact-path) artifact_path=$2; shift 2 ;;
        --output-path) output_path=$2; shift 2 ;;
        --exclude-pipeline-id) exclude_pipeline_id=$2; shift 2 ;;
        --status-output-path) status_output_path=$2; shift 2 ;;
        --directory) directory=true; shift ;;
        --optional) optional=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
    esac
done

if [[ -z "${ref}" || -z "${job_name}" || -z "${artifact_path}" || -z "${output_path}" ]]; then
    usage
    exit 1
fi

api_url=${GITLAB_API_V4_URL:-${CI_API_V4_URL:-}}
project_id=${GITLAB_PROJECT_ID:-${CI_PROJECT_ID:-}}
job_token=${GITLAB_JOB_TOKEN:-${CI_JOB_TOKEN:-}}
private_token=${GITLAB_PRIVATE_TOKEN:-${PRIVATE_TOKEN:-${GITLAB_TOKEN:-}}}

if [[ -z "${api_url}" || -z "${project_id}" ]]; then
    echo "Missing GitLab API URL or project ID." >&2
    exit 1
fi

if [[ -n "${job_token}" ]]; then
    auth_header="JOB-TOKEN: ${job_token}"
elif [[ -n "${private_token}" ]]; then
    auth_header="PRIVATE-TOKEN: ${private_token}"
else
    echo "Missing GitLab token." >&2
    exit 1
fi

jq_job_name_args=(
    --arg job_name "${job_name}"
    --arg dane_params "${DANE_PARAMS:-}"
    --arg matrix_params "${MATRIX_PARAMS:-}"
    --arg elcap_params "${ELCAP_PARAMS:-}"
    --arg gpumode "${GPUMODE:-}"
)
# shellcheck disable=SC2016
jq_normalize_job_name='
    def normalize_job_name:
        gsub("\\$\\{DANE_PARAMS\\}|\\$DANE_PARAMS"; $dane_params)
        | gsub("\\$\\{MATRIX_PARAMS\\}|\\$MATRIX_PARAMS"; $matrix_params)
        | gsub("\\$\\{ELCAP_PARAMS\\}|\\$ELCAP_PARAMS"; $elcap_params)
        | gsub("\\$\\{GPUMODE\\}|\\$GPUMODE"; $gpumode);
'

pipelines_json=$(
    curl --silent --show-error --fail --get \
        --header "${auth_header}" \
        --data-urlencode "ref=${ref}" \
        --data-urlencode "order_by=id" \
        --data-urlencode "sort=desc" \
        --data-urlencode "per_page=100" \
        "${api_url}/projects/${project_id}/pipelines"
)

candidate_pipelines=$(
    printf '%s' "${pipelines_json}" \
    | jq -r --arg exclude_pipeline_id "${exclude_pipeline_id}" '
        [.[] | select($exclude_pipeline_id == "" or (.id | tostring) != $exclude_pipeline_id)]
        | sort_by(.id)
        | reverse[]
        | .id
    '
)

job_id=""
job_status=""

while read -r pipeline_id; do
    [[ -z "${pipeline_id}" ]] && continue

    jobs_json=$(
        curl --silent --show-error --fail \
            --header "${auth_header}" \
            "${api_url}/projects/${project_id}/pipelines/${pipeline_id}/jobs?per_page=100"
    )

    job_id=$(
        printf '%s' "${jobs_json}" \
        | jq -r "${jq_job_name_args[@]}" "${jq_normalize_job_name}"'
            [.[] | select((.name | normalize_job_name) == ($job_name | normalize_job_name) and (.artifacts_file.filename // "") != "")]
            | sort_by(.id)
            | last
            | .id // empty
        '
    )
    [[ -z "${job_id}" ]] && continue

    job_status=$(
        printf '%s' "${jobs_json}" \
        | jq -r --arg job_id "${job_id}" '.[] | select((.id | tostring) == $job_id) | .status'
    )
    break
done <<< "${candidate_pipelines}"

if [[ -z "${job_id}" ]]; then
    if [[ "${optional}" == true ]]; then
        echo "No matching job with artifacts found for optional artifact ${artifact_path}."
        exit 0
    fi
    echo "Unable to locate job '${job_name}' with artifacts for ref ${ref}." >&2
    exit 1
fi

if [[ -n "${status_output_path}" ]]; then
    mkdir -p "$(dirname "${status_output_path}")"
    printf '%s\n' "${job_status}" > "${status_output_path}"
fi

artifact_archive=$(mktemp)
trap 'rm -f "${artifact_archive}"' EXIT

curl --location --silent --show-error --fail \
    --header "${auth_header}" \
    "${api_url}/projects/${project_id}/jobs/${job_id}/artifacts" \
    --output "${artifact_archive}"

if [[ "${directory}" == true ]]; then
    prefix="${artifact_path%/}/"
    mkdir -p "${output_path}"
    matches=$(unzip -Z -1 "${artifact_archive}" "${prefix}*" 2>/dev/null | grep -v '/$' || true)

    if [[ -z "${matches}" ]]; then
        if [[ "${optional}" == true ]]; then
            echo "No optional artifacts found under ${artifact_path}."
            exit 0
        fi
        echo "Unable to locate artifact directory ${artifact_path}." >&2
        exit 1
    fi

    while read -r member; do
        relative_path=${member#"${prefix}"}
        destination="${output_path}/${relative_path}"
        mkdir -p "$(dirname "${destination}")"
        unzip -p "${artifact_archive}" "${member}" > "${destination}"
    done <<< "${matches}"
else
    mkdir -p "$(dirname "${output_path}")"
    if ! unzip -p "${artifact_archive}" "${artifact_path}" > "${output_path}" 2>/dev/null; then
        rm -f "${output_path}"
        if [[ "${optional}" == true ]]; then
            echo "Optional artifact ${artifact_path} was not found."
            exit 0
        fi
        echo "Unable to locate artifact ${artifact_path}." >&2
        exit 1
    fi
fi

echo "Fetched ${artifact_path} from job ${job_id} (status=${job_status}) to ${output_path}"
