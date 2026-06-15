#!/bin/bash
set -euo pipefail

if [[ $# -lt 5 || $# -gt 7 ]]; then
    echo "Usage: $0 <ref> <job_name> <host> <benchmark> <output_path> [exclude_pipeline_id] [status_output_path]" >&2
    exit 1
fi

ref=$1
job_name=$2
host=$3
benchmark=$4
output_path=$5
exclude_pipeline_id=${6:-}
status_output_path=${7:-}

api_url=${GITLAB_API_V4_URL:-${CI_API_V4_URL:-}}
project_id=${GITLAB_PROJECT_ID:-${CI_PROJECT_ID:-}}
job_token=${GITLAB_JOB_TOKEN:-${CI_JOB_TOKEN:-}}
private_token=${GITLAB_PRIVATE_TOKEN:-${PRIVATE_TOKEN:-${GITLAB_TOKEN:-}}}
artifact_relpath="artifact-githash/${host}/${benchmark}/githash_metadata.json"

if [[ -z "${api_url}" ]]; then
    echo "Missing GitLab API URL. Set GITLAB_API_V4_URL or CI_API_V4_URL." >&2
    exit 1
fi

if [[ -z "${project_id}" ]]; then
    echo "Missing GitLab project ID. Set GITLAB_PROJECT_ID or CI_PROJECT_ID." >&2
    exit 1
fi

if [[ -n "${job_token}" ]]; then
    auth_header="JOB-TOKEN: ${job_token}"
elif [[ -n "${private_token}" ]]; then
    auth_header="PRIVATE-TOKEN: ${private_token}"
else
    echo "Missing GitLab token. Set GITLAB_JOB_TOKEN/CI_JOB_TOKEN or GITLAB_PRIVATE_TOKEN/PRIVATE_TOKEN/GITLAB_TOKEN." >&2
    exit 1
fi

echo "Searching ref '${ref}' for artifact '${artifact_relpath}'"
if [[ -n "${exclude_pipeline_id}" ]]; then
    echo "Excluding pipeline ID ${exclude_pipeline_id}"
fi

pipelines_json=$(
    curl --silent --show-error --fail --get \
        --header "${auth_header}" \
        --data-urlencode "ref=${ref}" \
        --data-urlencode "order_by=id" \
        --data-urlencode "sort=desc" \
        --data-urlencode "per_page=20" \
        "${api_url}/projects/${project_id}/pipelines"
)

echo "Candidate pipelines:"
printf '%s' "${pipelines_json}" | jq -r '
    if length == 0 then
        "  (none)"
    else
        .[] | "  id=\(.id) status=\(.status) ref=\(.ref) sha=\(.sha)"
    end
'

baseline_pipeline_id=$(
    printf '%s' "${pipelines_json}" \
    | jq -r --arg exclude_pipeline_id "${exclude_pipeline_id}" '
        [.[] | select($exclude_pipeline_id == "" or (.id | tostring) != $exclude_pipeline_id)]
        | sort_by(.id)
        | last
        | .id // empty
    '
)

if [[ -z "${baseline_pipeline_id}" ]]; then
    echo "Unable to locate a candidate pipeline for ref ${ref} after exclusions." >&2
    exit 1
fi

echo "Selected pipeline ID ${baseline_pipeline_id}"

jobs_json=$(
    curl --silent --show-error --fail \
        --header "${auth_header}" \
        "${api_url}/projects/${project_id}/pipelines/${baseline_pipeline_id}/jobs?per_page=100"
)

echo "Matching jobs in pipeline ${baseline_pipeline_id}:"
printf '%s' "${jobs_json}" | jq -r --arg job_name "${job_name}" '
    [ .[] | select(.name == $job_name) ] as $matches
    | if ($matches | length) == 0 then
        "  (none)"
      else
        $matches[]
        | "  id=\(.id) status=\(.status) artifacts=\((.artifacts_file.filename // "<none>"))"
      end
'

baseline_job_id=$(
    printf '%s' "${jobs_json}" \
    | jq -r --arg job_name "${job_name}" '
        [.[] | select(.name == $job_name and (.artifacts_file.filename // "") != "")]
        | sort_by(.id)
        | last
        | .id // empty
    '
)

baseline_job_status=$(
    printf '%s' "${jobs_json}" \
    | jq -r --arg job_name "${job_name}" '
        [.[] | select(.name == $job_name and (.artifacts_file.filename // "") != "")]
        | sort_by(.id)
        | last
        | .status // empty
    '
)

if [[ -z "${baseline_job_id}" ]]; then
    echo "Unable to locate job '${job_name}' with artifacts in pipeline ${baseline_pipeline_id}." >&2
    exit 1
fi

if [[ -z "${baseline_job_status}" ]]; then
    echo "Unable to determine status for job '${job_name}' in pipeline ${baseline_pipeline_id}." >&2
    exit 1
fi

mkdir -p "$(dirname "${output_path}")"

if [[ -n "${status_output_path}" ]]; then
    mkdir -p "$(dirname "${status_output_path}")"
    printf '%s\n' "${baseline_job_status}" > "${status_output_path}"
fi

curl --location --silent --show-error --fail \
    --header "${auth_header}" \
    "${api_url}/projects/${project_id}/jobs/${baseline_job_id}/artifacts/${artifact_relpath}" \
    --output "${output_path}"

echo "Downloaded artifact from pipeline ${baseline_pipeline_id}, job ${baseline_job_id} (status=${baseline_job_status}) to ${output_path}"
