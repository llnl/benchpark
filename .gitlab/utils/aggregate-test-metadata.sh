#!/bin/bash
set -euo pipefail

input_dir="collected-test-metadata"
output_path="artifact-test-summary/test_metadata_summary.json"
output_dir="$(dirname "${output_path}")"
ref="${CI_COMMIT_REF_NAME:-}"
artifact_path="artifact-test-metadata/test_metadata.json"
pipeline_id="${CI_PIPELINE_ID:-}"
summary_date="${CI_PIPELINE_CREATED_AT:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}"
git_sha="${CI_COMMIT_SHA:-$(git rev-parse HEAD 2>/dev/null || true)}"

mkdir -p "${output_dir}"

if [[ -z "${pipeline_id}" || -z "${ref}" ]]; then
    echo "Missing pipeline ID or ref." >&2
    exit 1
fi

bash .gitlab/utils/fetch-job-artifact.sh \
    --ref "${ref}" \
    --pipeline-id "${pipeline_id}" \
    --pipeline-stage test \
    --artifact-path "${artifact_path}" \
    --output-path "${input_dir}" \
    --optional

metadata_files=()
while IFS= read -r -d '' metadata_file; do
    metadata_files+=("${metadata_file}")
done < <(find "${input_dir}" -maxdepth 1 -type f -name '*.json' -print0 | sort -z)

if [[ ${#metadata_files[@]} -eq 0 ]]; then
    jq -n \
        --arg pipeline_id "${CI_PIPELINE_ID:-}" \
        --arg ref "${CI_COMMIT_REF_NAME:-}" \
        --arg date "${summary_date}" \
        --arg gitSHA "${git_sha}" \
        '{
          pipeline_id: $pipeline_id,
          ref: $ref,
          date: $date,
          gitSHA: $gitSHA,
          results: []
        }' > "${output_path}"
    exit 0
fi

for metadata_file in "${metadata_files[@]}"; do
    host="$(jq -r '.host // empty' "${metadata_file}" | tr '[:upper:]' '[:lower:]')"
    if [[ -n "${host}" ]]; then
        mkdir -p "${output_dir}/${host}"
        jq \
            --arg date "${summary_date}" \
            --arg gitSHA "${git_sha}" \
            '. + {date: $date, gitSHA: $gitSHA}' \
            "${metadata_file}" > "${output_dir}/${host}/$(basename "${metadata_file}")"
    fi
done

jq -s \
    --arg pipeline_id "${CI_PIPELINE_ID:-}" \
    --arg ref "${CI_COMMIT_REF_NAME:-}" \
    --arg date "${summary_date}" \
    --arg gitSHA "${git_sha}" \
    'sort_by([.host // "", .benchmark // "", .variant // "", .job.name // ""]) as $results
     | {
         pipeline_id: $pipeline_id,
         ref: $ref,
         date: $date,
         gitSHA: $gitSHA,
         results: $results
       }' "${metadata_files[@]}" > "${output_path}"
