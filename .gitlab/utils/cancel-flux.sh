#!/bin/bash
set -x

NO_CLEAN=false
if [[ "$1" == "--no-clean" ]]; then
    NO_CLEAN=true
fi

export URI=$(flux jobs -o "{id} {name}" | grep ${ALLOC_NAME}${GPUMODE} | awk '{print $1}')
([[ -n "${URI}" ]] && flux cancel ${URI} || true)
if [[ -n "${URI}" ]]; then
    for i in {1..60}; do
        WAITING=false
        for id in ${URI}; do
            if flux jobs -o "{id}" | grep -Fxq "${id}"; then
                WAITING=true
            fi
        done
        $WAITING || break
        echo "Waiting for Flux job ${URI} to stop before cleanup"
        sleep 5
    done
fi

echo "CLEANING CHECK"
if ! $NO_CLEAN; then
    CLEANUP_CI_BUILDS_DIR="${CUSTOM_CI_BUILDS_DIR/#\$HOME/$HOME}"
    CLEANUP_LOCK_DIR="${CLEANUP_CI_BUILDS_DIR}.cleanup.lock"
    if mkdir "$CLEANUP_LOCK_DIR"; then
        echo "Removing $CLEANUP_CI_BUILDS_DIR"
        rm -rf "$CLEANUP_CI_BUILDS_DIR"
        rm_rc=$?
        echo "rm exit code: $rm_rc"
        if [[ -e "$CLEANUP_CI_BUILDS_DIR" ]]; then
            echo "Cleanup target still exists immediately after rm"
            find "$CLEANUP_CI_BUILDS_DIR" -maxdepth 4 -mindepth 1 | head -100 || true
        else
            echo "Cleanup target removed immediately after rm"
        fi
        rmdir "$CLEANUP_LOCK_DIR" || true
    else
        echo "Cleanup already running for $CLEANUP_CI_BUILDS_DIR"
    fi
fi
