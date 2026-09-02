#!/bin/bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <checkout_label> <run_status_file>" >&2
    exit 1
fi

checkout_label=$1
run_status_file=$2

run_workspace="${CI_PROJECT_DIR}/wkp/${HOST}/${BENCHMARK}/workspace"
artifact_dir="${CI_PROJECT_DIR}/artifact-githash"
githash_json=""
artifact_githash_json="${artifact_dir}/githash_metadata.json"
baseline_json="${artifact_dir}/baseline_githash_metadata.json"
baseline_status_file="${artifact_dir}/baseline_job.status"
githash_status="NOT_FOUND"
baseline_githash_status="NOT_FOUND"

generate_githash_metadata() {
    local setup_script="${CI_PROJECT_DIR}/wkp/setup.sh"
    local spack_yaml=""
    local spack_env_dir=""

    if [[ ! -f "${setup_script}" ]]; then
        echo "Unable to locate Benchpark setup script at ${setup_script}" >&2
        return 1
    fi

    if [[ -d "${run_workspace}/software/spack" ]]; then
        spack_yaml=$(find "${run_workspace}/software/spack" -type f -path "*/${BENCHMARK}/spack.yaml" | sort | sed -n '1p')
        if [[ -z "${spack_yaml}" ]]; then
            spack_yaml=$(find "${run_workspace}/software/spack" -type f -name 'spack.yaml' | sort | sed -n '1p')
        fi
    fi

    if [[ -z "${spack_yaml}" ]]; then
        echo "Unable to locate Spack environment under ${run_workspace}/software/spack" >&2
        return 1
    fi

    spack_env_dir=$(dirname "${spack_yaml}")

    # shellcheck disable=SC1090
    . "${setup_script}" || return 1
    spack env activate "${spack_env_dir}" || return 1
    python "${CI_PROJECT_DIR}/modifiers/githash/githash.py" \
        "${artifact_githash_json}" \
        "${CI_PROJECT_DIR}" \
        "${BENCHMARK}" || return 1
}

if [[ -d "${run_workspace}/experiments" ]]; then
    githash_json=$(find "${run_workspace}/experiments" -type f -name 'githash_metadata.json' | sort | sed -n '1p')
fi

mkdir -p "${artifact_dir}"
if [[ -n "${githash_json}" ]]; then
    cp "${githash_json}" "${artifact_githash_json}"
    githash_status="FOUND"
else
    echo "Unable to locate ${checkout_label} githash metadata in ${run_workspace}" >&2
    if generate_githash_metadata; then
        githash_json="${artifact_githash_json}"
        githash_status="FOUND"
    fi
fi

fetch_args=(
    --ref "${BASELINE_REF}"
    --job-name "${CI_JOB_NAME}"
    --artifact-path "artifact-githash/githash_metadata.json"
    --output-path "${baseline_json}"
    --exclude-pipeline-id "${CI_PIPELINE_ID}"
    --status-output-path "${baseline_status_file}"
)

if bash .gitlab/utils/fetch-job-artifact.sh "${fetch_args[@]}"; then
    baseline_githash_status="FOUND"
fi

if [[ "$(cat "${run_status_file}")" == "0" ]]; then
    run_status="PASSED"
else
    run_status="FAILED"
fi

baseline_status="NOT_FOUND"
if [[ -f "${baseline_status_file}" ]]; then
    case "$(cat "${baseline_status_file}")" in
        success)
            baseline_status="PASSED"
            ;;
        failed)
            baseline_status="FAILED"
            ;;
        canceled)
            baseline_status="CANCELED"
            ;;
        running)
            baseline_status="RUNNING"
            ;;
        pending)
            baseline_status="PENDING"
            ;;
        manual)
            baseline_status="MANUAL"
            ;;
        skipped)
            baseline_status="SKIPPED"
            ;;
        created)
            baseline_status="CREATED"
            ;;
        waiting_for_resource)
            baseline_status="WAITING_FOR_RESOURCE"
            ;;
        preparing)
            baseline_status="PREPARING"
            ;;
        scheduled)
            baseline_status="SCHEDULED"
            ;;
        *)
            baseline_status="$(tr '[:lower:]' '[:upper:]' < "${baseline_status_file}")"
            ;;
    esac
fi

echo -e "===============[TESTS]==============="
echo "[Baseline]: ${baseline_status}, githash ${baseline_githash_status}"
echo "[${checkout_label}]: ${run_status}, githash ${githash_status}"
echo -e "====================================="
if [[ "${baseline_githash_status}" == "FOUND" && "${githash_status}" == "FOUND" ]]; then
    bash .gitlab/utils/compare-githash-metadata.sh "${baseline_json}" "${githash_json}"
else
    exit 1
fi
