#!/bin/bash
set -euo pipefail

run_workspace="${CI_PROJECT_DIR}/wkp/${HOST}/${BENCHMARK}/workspace"
artifact_dir="${CI_PROJECT_DIR}/artifact-cali"
baseline_artifact_dir="${CI_PROJECT_DIR}/baseline-cali"
performance_json="${artifact_dir}/performance_metadata.json"
baseline_performance_json="${baseline_artifact_dir}/performance_metadata.json"
performance_metric="Avg time/rank"
performance_region="main"
performance_threshold="0.05"

mkdir -p "${artifact_dir}"
mkdir -p "${baseline_artifact_dir}"

. /usr/workspace/benchpark-dev/benchpark-venv/$SYS_TYPE/bin/activate

write_unavailable_performance() {
    local reason=$1
    jq -n \
        --arg reason "${reason}" \
        --arg metric "${performance_metric}" \
        --arg region "${performance_region}" \
        '{
          available: false,
          reason: $reason,
          metric: $metric,
          region: $region,
          regressed: false
        }' > "${performance_json}"
}

write_unavailable_performance "No Caliper artifacts found"

if [[ -d "${run_workspace}/experiments" ]]; then
    find "${run_workspace}/experiments" -type f -name '*.cali' -exec cp {} "${artifact_dir}/" \; || true
else
    echo "Unable to locate experiments directory in ${run_workspace}; no Caliper artifacts collected."
fi

if find "${artifact_dir}" -maxdepth 1 -type f -name '*.cali' | grep -q .; then
    query_dir=$(mktemp -d)
    trap 'rm -rf "${query_dir}"' EXIT
    find "${artifact_dir}" -maxdepth 1 -type f -name '*.cali' -exec cp {} "${query_dir}/" \; || true

    if (
        cd "${query_dir}"
        "${CI_PROJECT_DIR}/bin/benchpark" query . \
            --metric "${performance_metric}" \
            --query-regions-byname "${performance_region}"
    ); then
        query_csv=$(find "${query_dir}" -maxdepth 1 -type f -name 'query-*.csv' | sort | tail -n 1)
        if [[ -n "${query_csv}" ]]; then
            performance_value=$(
                awk -F, '
                    /^[[:space:]]*#/ || /^[[:space:]]*$/ || $1 == "cluster" { next }
                    NF >= 3 { print $3; exit }
                ' "${query_csv}"
            )
            if [[ "${performance_value:-}" =~ ^[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?$ ]]; then
                jq -n \
                    --arg metric "${performance_metric}" \
                    --arg region "${performance_region}" \
                    --argjson value "${performance_value}" \
                    '{
                      available: true,
                      metric: $metric,
                      region: $region,
                      value: $value,
                      regressed: false
                    }' > "${performance_json}"
            else
                write_unavailable_performance "Unable to parse performance value"
            fi
        else
            write_unavailable_performance "benchpark query did not produce a query CSV"
        fi
    else
        write_unavailable_performance "benchpark query failed"
    fi
fi

if [[ "$(jq -r '.available // false' "${performance_json}")" == "true" && -n "${BASELINE_REF:-}" && -n "${CI_JOB_NAME:-}" ]]; then
    bash .gitlab/utils/fetch-job-artifact.sh \
        --ref "${BASELINE_REF}" \
        --job-name "${CI_JOB_NAME}" \
        --artifact-path "artifact-cali/performance_metadata.json" \
        --output-path "${baseline_performance_json}" \
        --exclude-pipeline-id "${CI_PIPELINE_ID:-}" \
        --optional

    if [[ -s "${baseline_performance_json}" ]]; then
        if current_performance_value="$(jq -er '.value | numbers' "${performance_json}" 2>/dev/null)" \
            && baseline_performance_value="$(jq -er 'select(.available == true) | .value | numbers' "${baseline_performance_json}" 2>/dev/null)"; then
            tmp_performance_json=$(mktemp)
            jq \
                --argjson baseline_value "${baseline_performance_value}" \
                --argjson threshold "${performance_threshold}" \
                '. + {
                  baseline_value: $baseline_value,
                  threshold: $threshold,
                  percent_deviation: (if $baseline_value > 0 then ((.value - $baseline_value) / $baseline_value * 100) else null end),
                  regressed: (if $baseline_value > 0 then (.value > ($baseline_value * (1 + $threshold))) else false end)
                }' "${performance_json}" > "${tmp_performance_json}"
            mv "${tmp_performance_json}" "${performance_json}"
        fi
    fi
fi
