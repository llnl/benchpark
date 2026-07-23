#!/bin/bash

NO_CLEAN=false
for arg in "$@"; do
    case "$arg" in
    --no-clean)
        NO_CLEAN=true
        ;;
    esac
done

JOBID=$(squeue -h --name=${ALLOC_NAME} --format=%A)
([[ -n "${JOBID}" ]] && scancel ${JOBID} || true)
if [[ -n "${JOBID}" ]]; then
    JOBIDS_CSV="${JOBID//$'\n'/,}"
    JOBIDS_CSV="${JOBIDS_CSV// /,}"
    for i in {1..60}; do
        squeue -h -j "${JOBIDS_CSV}" | grep -q . || break
        echo "Waiting for Slurm job ${JOBID} to stop before cleanup"
        sleep 5
    done
fi

if ! $NO_CLEAN; then
    bash .gitlab/utils/cancel-cleanup.sh "$CUSTOM_CI_BUILDS_DIR"
fi
