#!/bin/bash
set -x

NO_CLEAN=false
if [[ "$1" == "--no-clean" ]]; then
    NO_CLEAN=true
fi

export JOBID=$(squeue -h --name=${ALLOC_NAME} --format=%A)
([[ -n "${JOBID}" ]] && scancel ${JOBID} || true)

echo "CLEANING CHECK"
if ! $NO_CLEAN; then
    CLEANUP_CI_BUILDS_DIR="${CUSTOM_CI_BUILDS_DIR/#\$HOME/$HOME}"
    CLEANUP_LOCK_DIR="${CLEANUP_CI_BUILDS_DIR}.cleanup.lock"
    if mkdir "$CLEANUP_LOCK_DIR" 2>/dev/null; then
        echo "Removing $CLEANUP_CI_BUILDS_DIR"
        rm -rf "$CLEANUP_CI_BUILDS_DIR"
        rmdir "$CLEANUP_LOCK_DIR" 2>/dev/null || true
    else
        echo "Cleanup already running for $CLEANUP_CI_BUILDS_DIR"
    fi
fi
