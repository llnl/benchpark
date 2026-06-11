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
            [{name: $packages.application.name, commit: $packages.application.commit}]
            + ($packages.dependencies | to_entries | map({name: .value.name, commit: .value.commit}))
          )
        | sort_by(.name)
        | .[]
        | [.name, .commit]
        | @tsv
    ' "$json_file"
}

echo -e "\n\n======[PACKAGE GITHASH SUMMARY]======="
while IFS=$'\t' read -r package_name old_commit; do
    new_commit=$(
        extract_packages "$new_json" | awk -F'\t' -v name="$package_name" '$1 == name { print $2; exit }'
    )
    
    if [[ -n "$new_commit" && "$old_commit" != "$new_commit" ]]; then
        echo "[${package_name}]: changed versions from ${old_commit} to ${new_commit}."
    else
        echo "[${package_name}]: has no commit changes."
    fi
done < <(extract_packages "$old_json")
echo -e "======================================\n\n"