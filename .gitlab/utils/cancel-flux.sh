#!/bin/bash
set -x
export URI=$(flux jobs -o "{id} {name}" | grep ${ALLOC_NAME}${GPUMODE} | awk '{print $1}')
([[ -n "${URI}" ]] && flux job kill ${URI} || exit 0)
echo "Removing $CUSTOM_CI_BUILDS_DIR"
rm -rf $CUSTOM_CI_BUILDS_DIR