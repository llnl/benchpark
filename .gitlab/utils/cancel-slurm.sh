#!/bin/bash
set -x

NO_CLEAN=false
if [[ "$1" == "--no-clean" ]]; then
    NO_CLEAN=true
fi

export JOBID=$(squeue -h --name=${ALLOC_NAME} --format=%A)
([[ -n "${JOBID}" ]] && scancel ${JOBID} || exit 0)

if ! $NO_CLEAN; then
    CLEANUP_CI_BUILDS_DIR="${CUSTOM_CI_BUILDS_DIR/#\$HOME/$HOME}"
    echo "Removing $CLEANUP_CI_BUILDS_DIR"
    rm -rf "$CLEANUP_CI_BUILDS_DIR"
fi
