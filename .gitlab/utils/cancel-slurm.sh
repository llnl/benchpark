#!/bin/bash
set -x
export JOBID=$(squeue -h --name=${ALLOC_NAME} --format=%A)
([[ -n "${JOBID}" ]] && scancel ${JOBID} || exit 0)
echo "Removing $CUSTOM_CI_BUILDS_DIR"
rm -rf $CUSTOM_CI_BUILDS_DIR