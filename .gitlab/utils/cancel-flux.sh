#!/bin/bash

NO_CLEAN=false
for arg in "$@"; do
    case "$arg" in
    --no-clean)
        NO_CLEAN=true
        ;;
    esac
done

URI=$(flux jobs -o "{id} {name}" | grep "${ALLOC_NAME}${GPUMODE}" | awk '{print $1}')
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

if ! $NO_CLEAN; then
    bash .gitlab/utils/cancel-cleanup.sh "$CUSTOM_CI_BUILDS_DIR"
fi
