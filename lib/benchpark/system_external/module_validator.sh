#!/bin/bash
# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

# Validate one module sequence in an isolated login shell.

python_exe=$1
shift

_emit() {
    "$python_exe" -c "$BENCHPARK_EXTERNAL_MODULE_EMITTER" "$1" "$2" "$3" "$4" "$5"
}

_loaded_modules() {
    module -t list 2>&1
}

if ! type module >/dev/null 2>&1; then
    _emit "validator_failed" "" "module command unavailable" "" ""
    exit 0
fi

module --force purge >/dev/null 2>&1
purge_status=$?
if [ "$purge_status" -ne 0 ]; then
    _emit "validator_failed" "" "module --force purge failed" "" ""
    exit 0
fi

for requested_module in "$@"; do
    module is-avail "$requested_module" >/dev/null 2>&1
    availability_status=$?
    if [ "$availability_status" -ne 0 ]; then
        loaded_modules=$(_loaded_modules)
        if [ "$availability_status" -eq 1 ]; then
            _emit "not_found" "$requested_module" "" "$loaded_modules" ""
        else
            _emit "validator_failed" "$requested_module" "module is-avail failed" "$loaded_modules" ""
        fi
        exit 0
    fi

    module load "$requested_module"
    load_status=$?
    if [ "$load_status" -ne 0 ]; then
        loaded_modules=$(_loaded_modules)
        _emit "module_load_failed" "$requested_module" "module load failed" "$loaded_modules" ""
        exit 0
    fi
done

loaded_modules=$(_loaded_modules)
loaded_status=$?
if [ "$loaded_status" -ne 0 ]; then
    _emit "validator_failed" "" "module list failed" "" ""
    exit 0
fi

spack_status=""
if [ -n "${BENCHPARK_SPACK_REQUEST:-}" ]; then
    printf '%s' "$BENCHPARK_SPACK_REQUEST" | \
        "$BENCHPARK_SPACK_EXECUTABLE" \
        -c "$BENCHPARK_SPACK_REPOSITORY_CONFIG" \
        python "$BENCHPARK_SPACK_HELPER"
    spack_status=$?
fi
_emit "valid" "" "" "$loaded_modules" "$spack_status"
