#!/bin/bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <checkout_label> <run_status_file>" >&2
    exit 1
fi

checkout_label=$1
run_status_file=$2

run_workspace="${CI_PROJECT_DIR}/wkp/${HOST}/${BENCHMARK}/workspace"
artifact_dir="${CI_PROJECT_DIR}/artifact-githash/${HOST}/${BENCHMARK}"
githash_json=""
baseline_json="${artifact_dir}/baseline_githash_metadata.json"
baseline_status_file="${artifact_dir}/baseline_job.status"

if [[ -d "${run_workspace}/experiments" ]]; then
    githash_json=$(find "${run_workspace}/experiments" -type f -name 'githash_metadata.json' | sort | sed -n '1p')
fi

mkdir -p "${artifact_dir}"
if [[ -n "${githash_json}" ]]; then
    cp "${githash_json}" "${artifact_dir}/githash_metadata.json"
else
    echo "Unable to locate ${checkout_label} githash metadata in ${run_workspace}" >&2
    exit 1
fi

fetch_args=(
    --ref "${BASELINE_REF}"
    --job-name "${CI_JOB_NAME}"
    --artifact-path "artifact-githash/${HOST}/${BENCHMARK}/githash_metadata.json"
    --output-path "${baseline_json}"
    --exclude-pipeline-id "${CI_PIPELINE_ID}"
    --status-output-path "${baseline_status_file}"
)

bash .gitlab/utils/fetch-job-artifact.sh "${fetch_args[@]}"

if [[ "$(cat "${run_status_file}")" == "0" ]]; then
    run_status="PASSED"
else
    run_status="FAILED"
fi

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

echo -e "===============[TESTS]==============="
echo "[Baseline]: ${baseline_status}"
echo "[${checkout_label}]: ${run_status}"
echo -e "====================================="
bash .gitlab/utils/compare-githash-metadata.sh "${baseline_json}" "${githash_json}"
