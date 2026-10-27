#!/bin/bash
set -euo pipefail

summary_dir="${CI_PROJECT_DIR}/artifact-test-summary"
perf_repo_url="${BENCHPARK_PERF_REPO_URL:-git@github.com:llnl/benchpark-performance.git}"
perf_repo_dir="$(mktemp -d)"
ssh_key_file="${perf_repo_dir}.ssh_key"
host_dirs=(dane tioga matrix tuolumne)

cleanup() {
    rm -rf "${perf_repo_dir}"
    rm -f "${ssh_key_file}"
}
trap cleanup EXIT

if [[ -z "${BENCHPARK_PERF_DEPLOY_TOKEN:-}" ]]; then
    echo "BENCHPARK_PERF_DEPLOY_TOKEN must contain the SSH private key for benchpark-performance." >&2
    exit 1
fi

if [[ ! -d "${summary_dir}" ]]; then
    echo "Missing nightly metadata directory: ${summary_dir}" >&2
    exit 1
fi

if [[ -f "${BENCHPARK_PERF_DEPLOY_TOKEN}" ]]; then
    cp "${BENCHPARK_PERF_DEPLOY_TOKEN}" "${ssh_key_file}"
else
    printf '%s\n' "${BENCHPARK_PERF_DEPLOY_TOKEN}" | tr -d '\r' > "${ssh_key_file}"
fi
chmod 600 "${ssh_key_file}"
git_ssh_command="ssh -i ${ssh_key_file} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"

GIT_SSH_COMMAND="${git_ssh_command}" GIT_TERMINAL_PROMPT=0 \
    git clone "${perf_repo_url}" "${perf_repo_dir}"

copied_hosts=()
for host in "${host_dirs[@]}"; do
    if [[ -d "${summary_dir}/${host}" ]] && find "${summary_dir}/${host}" -maxdepth 1 -type f -name '*.json' | grep -q .; then
        mkdir -p "${perf_repo_dir}/${host}"
        find "${summary_dir}/${host}" -maxdepth 1 -type f -name '*.json' -exec cp {} "${perf_repo_dir}/${host}/" \;
        copied_hosts+=("${host}")
    fi
done

if [[ "${#copied_hosts[@]}" -eq 0 ]]; then
    echo "No host metadata JSON files found in ${summary_dir}; nothing to deploy."
    exit 0
fi

cd "${perf_repo_dir}"

if [[ -z "$(git status --porcelain -- "${copied_hosts[@]}")" ]]; then
    echo "No benchpark-performance metadata changes to commit."
    exit 0
fi

git config user.name "${GITLAB_USER_NAME:-benchpark-ci}"
git config user.email "${GITLAB_USER_EMAIL:-benchpark-ci@llnl.gov}"

git add "${copied_hosts[@]}"
git commit -m "Update nightly performance metadata from ${CI_PIPELINE_ID:-unknown}"
GIT_SSH_COMMAND="${git_ssh_command}" GIT_TERMINAL_PROMPT=0 \
    git push origin HEAD
