#!/bin/bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <checkout_label> <run_status_file>" >&2
    exit 1
fi

checkout_label=$1
run_status_file=$2

artifact_dir="${CI_PROJECT_DIR}/artifact-test-status"
test_status_file="${CI_PROJECT_DIR}/test_status.txt"
githash_artifact_dir="${CI_PROJECT_DIR}/artifact-githash"
githash_changes_json="${githash_artifact_dir}/githash_changes.json"

mkdir -p "${artifact_dir}"

test_status="Unknown"
if [[ -f "${test_status_file}" ]]; then
    test_status="$(cat "${test_status_file}")"
fi

run_exit_code=""
if [[ -f "${run_status_file}" ]]; then
    run_exit_code="$(cat "${run_status_file}")"
fi

changes_json=$(mktemp)
if [[ -f "${githash_changes_json}" ]]; then
    cp "${githash_changes_json}" "${changes_json}"
else
    jq -n \
        --arg reason "Missing githash change summary" \
        '{available: false, reason: $reason, application_changed: false, dependencies_changed: false, packages: []}' \
        > "${changes_json}"
fi

jq -n \
    --arg checkout "${checkout_label}" \
    --arg host "${HOST:-}" \
    --arg benchmark "${BENCHMARK:-}" \
    --arg variant "${VARIANT:-}" \
    --arg system_args "${SYSTEM_ARGS:-}" \
    --arg benchmark_version "${BENCHMARK_VERSION:-}" \
    --arg status "${test_status}" \
    --arg run_exit_code "${run_exit_code}" \
    --arg job_name "${CI_JOB_NAME:-}" \
    --arg job_id "${CI_JOB_ID:-}" \
    --arg job_url "${CI_JOB_URL:-}" \
    --arg pipeline_id "${CI_PIPELINE_ID:-}" \
    --slurpfile changes "${changes_json}" \
    '{
      checkout: $checkout,
      host: $host,
      benchmark: $benchmark,
      variant: $variant,
      system_args: $system_args,
      benchmark_version: $benchmark_version,
      status: $status,
      run_exit_code: (if $run_exit_code == "" then null else ($run_exit_code | tonumber?) end),
      changes: $changes[0],
      job: {
        name: $job_name,
        id: $job_id,
        url: $job_url,
        pipeline_id: $pipeline_id
      }
    }' > "${artifact_dir}/test_status.json"

rm -f "${changes_json}"
