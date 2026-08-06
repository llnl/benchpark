#!/bin/bash
set -euo pipefail

input_dir="collected-test-metadata"
output_path="artifact-test-summary/test_metadata_summary.json"
ref="${CI_COMMIT_REF_NAME:-}"
artifact_path="artifact-test-metadata/test_metadata.json"
pipeline_id="${CI_PIPELINE_ID:-}"

mkdir -p "$(dirname "${output_path}")"

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
        '{
          pipeline_id: $pipeline_id,
          ref: $ref,
          results: []
        }' > "${output_path}"
    exit 0
fi

jq -s \
    --arg pipeline_id "${CI_PIPELINE_ID:-}" \
    --arg ref "${CI_COMMIT_REF_NAME:-}" \
    'sort_by([.host // "", .benchmark // "", .variant // "", .job.name // ""]) as $results
     | {
         pipeline_id: $pipeline_id,
         ref: $ref,
         results: $results
       }' "${metadata_files[@]}" > "${output_path}"
