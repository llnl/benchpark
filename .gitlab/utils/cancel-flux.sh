#!/bin/bash
set -x

NO_CLEAN=false
if [[ "$1" == "--no-clean" ]]; then
    NO_CLEAN=true
fi

export URI=$(flux jobs -o "{id} {name}" | grep ${ALLOC_NAME}${GPUMODE} | awk '{print $1}')
([[ -n "${URI}" ]] && flux cancel ${URI} || exit 0)

if ! $NO_CLEAN; then
    rm -rf $CUSTOM_CI_BUILDS_DIR
fi
