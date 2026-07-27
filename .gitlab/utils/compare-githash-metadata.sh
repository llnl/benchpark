#!/bin/bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <old_json> <new_json>" >&2
    exit 1
fi

old_json=$1
new_json=$2

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
            [{name: $packages.application.name, version: $packages.application.version, commit: $packages.application.commit}]
            + ($packages.dependencies | to_entries | map({name: .value.name, version: .value.version, commit: .value.commit}))
          )
        | .[]
        | [.name, (.version // "unknown"), (.commit // "none")]
        | @tsv
    ' "$json_file"
}

echo -e "======[PACKAGE GITHASH SUMMARY]======"
while IFS=$'\t' read -r package_name old_version old_commit; do
    new_package=$(
        extract_packages "$new_json" | awk -F'\t' -v name="$package_name" '$1 == name { print $2 "\t" $3; exit }'
    )
    IFS=$'\t' read -r new_version new_commit <<< "$new_package"

    if [[ -n "$new_version" && "$old_version" != "$new_version" ]]; then
        echo "[${package_name}]: changed versions from ${old_version} to ${new_version}."
    else
        echo "[${package_name}]: has no version changes."
    fi

    if [[ -n "$new_commit" && "$old_commit" != "$new_commit" ]]; then
        echo "[${package_name}]: changed commits from ${old_commit} to ${new_commit}."
    else
        echo "[${package_name}]: has no commit changes."
        echo
    fi
done < <(extract_packages "$old_json")
echo -e "====================================="
