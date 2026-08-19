#!/bin/bash
set -euo pipefail

run_workspace="${CI_PROJECT_DIR}/wkp/${HOST}/${BENCHMARK}/workspace"
artifact_dir="${CI_PROJECT_DIR}/artifact-cali"
baseline_artifact_dir="${CI_PROJECT_DIR}/baseline-cali"

mkdir -p "${artifact_dir}"
if [[ -d "${run_workspace}/experiments" ]]; then
    find "${run_workspace}/experiments" -type f -name '*.cali' -exec cp {} "${artifact_dir}/" \; || true
else
    echo "Unable to locate experiments directory in ${run_workspace}; no Caliper artifacts collected."
fi

bash .gitlab/utils/fetch-job-artifact.sh \
    --ref "${BASELINE_REF}" \
    --job-name "${CI_JOB_NAME}" \
    --artifact-path "artifact-cali/" \
    --output-path "${baseline_artifact_dir}" \
    --exclude-pipeline-id "${CI_PIPELINE_ID}" \
    --directory \
    --optional
