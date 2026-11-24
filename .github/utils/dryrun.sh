# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

#!/bin/bash

set -e

benchmark_spec="$1"
system_spec="$2"

benchpark_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
workspace_root="$benchpark_root/workspace"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/benchpark-dryrun.XXXXXXXXXXXX")"
cleanup() {
    status=$?
    if [ "$status" -eq 0 ]; then
        rm -rf "$work_dir"
    else
        echo "Dryrun files retained in $work_dir" >&2
    fi
}
trap cleanup EXIT
cd "$work_dir"

benchmark="benchmark"
system="s-${work_dir##*.}"
"$benchpark_root/bin/benchpark" system init --dest="$system" $system_spec
"$benchpark_root/bin/benchpark" experiment init --dest="$benchmark" "$system" $benchmark_spec
mkdir -p "$workspace_root"
python3 "$benchpark_root/.github/utils/locked_setup.py" \
    "$workspace_root" "$work_dir/$system/$benchmark/ramble.yaml" \
    "$benchpark_root/bin/benchpark" setup "./$system/$benchmark" "$workspace_root"
# The shared setup.sh reflects whichever package manager initialized it first.
if [ -f "$workspace_root/spack/share/spack/setup-env.sh" ]; then
    export SPACK_USER_CACHE_PATH="$workspace_root/spack-cache"
    export SPACK_DISABLE_LOCAL_CONFIG=1
    . "$workspace_root/spack/share/spack/setup-env.sh"
fi
. "$workspace_root/ramble/share/ramble/setup-env.sh"
ramble \
    --workspace-dir "$workspace_root/$system/$benchmark/workspace" \
    --disable-logger \
    workspace setup --dry-run
