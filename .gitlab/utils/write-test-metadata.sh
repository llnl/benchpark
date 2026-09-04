#!/bin/bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <checkout_label> <run_status_file>" >&2
    exit 1
fi

checkout_label=$1
run_status_file=$2

artifact_dir="${CI_PROJECT_DIR}/artifact-test-metadata"
test_status_file="${CI_PROJECT_DIR}/test_status.txt"
githash_artifact_dir="${CI_PROJECT_DIR}/artifact-githash"
githash_changes_json="${githash_artifact_dir}/githash_changes.json"
performance_json="${CI_PROJECT_DIR}/artifact-cali/performance_metadata.json"

mkdir -p "${artifact_dir}"

test_status="Not Tested"
if [[ -f "${test_status_file}" ]]; then
    test_status="$(cat "${test_status_file}")"
fi

run_exit_code=""
if [[ -f "${run_status_file}" ]]; then
    run_exit_code="$(cat "${run_status_file}")"
fi

if [[ ! -f "${test_status_file}" && -n "${run_exit_code}" && "${run_exit_code}" != "0" ]]; then
    test_status="Unknown"
fi

changes_json=$(mktemp)
changed_files_json=$(mktemp)
merged_performance_json=$(mktemp)
if [[ -f "${githash_changes_json}" ]]; then
    cp "${githash_changes_json}" "${changes_json}"
else
    jq -n \
        --arg reason "Missing githash change summary" \
        '{available: false, reason: $reason, application_changed: false, dependencies_changed: false, packages: []}' \
        > "${changes_json}"
fi

if [[ -s "${performance_json}" ]]; then
    cp "${performance_json}" "${merged_performance_json}"
else
    jq -n \
        --arg reason "Missing performance metadata" \
        '{
          available: false,
          reason: $reason,
          regressed: false
        }' > "${merged_performance_json}"
fi

printf '[]\n' > "${changed_files_json}"
diff_base="origin/${BASELINE_REF:-develop}"
if git rev-parse --verify --quiet "${diff_base}^{commit}" >/dev/null; then
    git diff --name-only "${diff_base}" HEAD 2>/dev/null \
        | jq -R -s 'split("\n") | map(select(length > 0))' \
        > "${changed_files_json}" \
        || printf '[]\n' > "${changed_files_json}"
fi

benchmark="${BENCHMARK:-}"
benchmark_application="${benchmark//-/_}"
application_spec_changed=false
experiment_spec_changed=false
system_spec_changed=false
if [[ -n "${benchmark}" ]]; then
    application_spec_changed="$(
        jq -r \
            --arg application_path "repos/ramble_applications/${benchmark_application}/" \
            --arg legacy_application_path "repos/applications/${benchmark}/" \
            'any(.[]; startswith($application_path) or startswith($legacy_application_path))' \
            "${changed_files_json}"
    )"
    experiment_spec_changed="$(
        jq -r \
            --arg experiment_path "experiments/${benchmark}/" \
            'any(.[]; startswith($experiment_path))' \
            "${changed_files_json}"
    )"
fi
if [[ -n "${ARCHCONFIG:-}" ]]; then
    system_spec_changed="$(
        jq -r \
            --arg system_path "systems/${ARCHCONFIG}/" \
            'any(.[]; startswith($system_path))' \
            "${changed_files_json}"
    )"
fi

status_changed=false
baseline_metadata_json=$(mktemp)
if [[ -n "${BASELINE_REF:-}" && -n "${CI_JOB_NAME:-}" ]]; then
    bash .gitlab/utils/fetch-job-artifact.sh \
        --ref "${BASELINE_REF}" \
        --job-name "${CI_JOB_NAME}" \
        --artifact-path "artifact-test-metadata/test_metadata.json" \
        --output-path "${baseline_metadata_json}" \
        --exclude-pipeline-id "${CI_PIPELINE_ID:-}" \
        --optional

    if [[ -s "${baseline_metadata_json}" ]]; then
        baseline_status="$(jq -r '.status // ""' "${baseline_metadata_json}")"
        if [[ -n "${baseline_status}" && "${baseline_status}" != "${test_status}" ]]; then
            status_changed=true
        fi
    fi
fi

jq -n \
    --arg checkout "${checkout_label}" \
    --arg host "${HOST:-}" \
    --arg benchmark "${BENCHMARK:-}" \
    --arg variant "${VARIANT:-}" \
    --arg system_args "${SYSTEM_ARGS:-}" \
    --arg benchmark_version "${BENCHMARK_VERSION:-}" \
    --arg status "${test_status}" \
    --argjson status_changed "${status_changed}" \
    --argjson application_spec_changed "${application_spec_changed}" \
    --argjson experiment_spec_changed "${experiment_spec_changed}" \
    --argjson system_spec_changed "${system_spec_changed}" \
    --arg run_exit_code "${run_exit_code}" \
    --arg job_name "${CI_JOB_NAME:-}" \
    --arg job_id "${CI_JOB_ID:-}" \
    --arg job_url "${CI_JOB_URL:-}" \
    --arg pipeline_id "${CI_PIPELINE_ID:-}" \
    --slurpfile changes "${changes_json}" \
    --slurpfile performance "${merged_performance_json}" \
    '{
      checkout: $checkout,
      host: $host,
      benchmark: $benchmark,
      variant: $variant,
      system_args: $system_args,
      benchmark_version: $benchmark_version,
      status: $status,
      status_changed: $status_changed,
      run_exit_code: (if $run_exit_code == "" then null else ($run_exit_code | tonumber?) end),
      changes: ($changes[0] + {
        application_spec_changed: $application_spec_changed,
        experiment_spec_changed: $experiment_spec_changed,
        system_spec_changed: $system_spec_changed
      }),
      performance: $performance[0],
      job: {
        name: $job_name,
        id: $job_id,
        url: $job_url,
        pipeline_id: $pipeline_id
      }
    }' > "${artifact_dir}/test_metadata.json"

rm -f "${changes_json}" "${changed_files_json}" "${merged_performance_json}" "${baseline_metadata_json}"
