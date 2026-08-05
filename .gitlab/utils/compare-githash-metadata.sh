#!/bin/bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
    echo "Usage: $0 <old_json> <new_json> [changes_json]" >&2
    exit 1
fi

old_json=$1
new_json=$2
changes_json=${3:-}

if [[ ! -f "$old_json" ]]; then
    echo "Missing file: $old_json" >&2
    exit 1
fi

if [[ ! -f "$new_json" ]]; then
    echo "Missing file: $new_json" >&2
    exit 1
fi

extract_packages() {
    local json_file=$1

    jq -r '
        .packages as $packages
        | (
            [{
                kind: "application",
                name: $packages.application.name,
                version: $packages.application.version,
                commit: $packages.application.commit
            }]
            + ($packages.dependencies | to_entries | map({
                kind: "dependency",
                name: .value.name,
                version: .value.version,
                commit: .value.commit
            }))
          )
        | .[]
        | [.kind, .name, (.version // "unknown"), (.commit // "none")]
        | @tsv
    ' "$json_file"
}

changed_packages_json=$(mktemp)
tmp_changes_json=""
trap 'rm -f "${changed_packages_json}" "${tmp_changes_json}"' EXIT
printf '[]\n' > "${changed_packages_json}"

echo -e "======[PACKAGE GITHASH SUMMARY]======"
while IFS=$'\t' read -r package_kind package_name old_version old_commit; do
    new_package=$(
        extract_packages "$new_json" | awk -F'\t' -v kind="$package_kind" -v name="$package_name" '$1 == kind && $2 == name { print $3 "\t" $4; exit }'
    )
    IFS=$'\t' read -r new_version new_commit <<< "$new_package"

    version_changed=false
    commit_changed=false

    if [[ -n "$new_version" && "$old_version" != "$new_version" ]]; then
        version_changed=true
        echo "[${package_name}]: changed versions from ${old_version} to ${new_version}."
    else
        echo "[${package_name}]: has no version changes."
    fi

    if [[ -n "$new_commit" && "$old_commit" != "$new_commit" ]]; then
        commit_changed=true
        echo "[${package_name}]: changed commits from ${old_commit} to ${new_commit}."
    else
        echo "[${package_name}]: has no commit changes."
        echo
    fi

    if [[ "${version_changed}" == "true" || "${commit_changed}" == "true" ]]; then
        tmp_changes_json=$(mktemp)
        jq \
            --arg kind "${package_kind}" \
            --arg name "${package_name}" \
            --arg old_version "${old_version}" \
            --arg new_version "${new_version}" \
            --arg old_commit "${old_commit}" \
            --arg new_commit "${new_commit}" \
            --argjson version_changed "${version_changed}" \
            --argjson commit_changed "${commit_changed}" \
            '. + [{
                kind: $kind,
                name: $name,
                old_version: $old_version,
                new_version: $new_version,
                old_commit: $old_commit,
                new_commit: $new_commit,
                version_changed: $version_changed,
                commit_changed: $commit_changed
            }]' "${changed_packages_json}" > "${tmp_changes_json}"
        mv "${tmp_changes_json}" "${changed_packages_json}"
        tmp_changes_json=""
    fi
done < <(extract_packages "$old_json")
echo -e "====================================="

if [[ -n "${changes_json}" ]]; then
    mkdir -p "$(dirname "${changes_json}")"
    jq '{
        available: true,
        application_changed: any(.[]; .kind == "application"),
        dependencies_changed: any(.[]; .kind == "dependency"),
        packages: .
    }' "${changed_packages_json}" > "${changes_json}"
fi
