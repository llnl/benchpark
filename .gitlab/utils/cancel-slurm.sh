#!/bin/bash

NO_CLEAN=false
for arg in "$@"; do
    case "$arg" in
    --no-clean)
        NO_CLEAN=true
        ;;
    esac
done

schedule_delayed_cleanup() {
    cleanup_script=$(printf '%s\n' \
        "lock=$(printf "%q" "$CLEANUP_LOCK_DIR")" \
        "target=$(printf "%q" "$CLEANUP_CI_BUILDS_DIR")" \
        '    rm -rf "$target"' \
        '    rmdir "$lock" 2>/dev/null || true')

    echo "Scheduling delayed cleanup for $CLEANUP_CI_BUILDS_DIR"
    if command -v at >/dev/null 2>&1 &&
        printf '%s\n' "$cleanup_script" | at now + 2 minutes >/dev/null 2>&1; then
        echo "Delayed cleanup queued with at"
        return 0
    elif command -v setsid >/dev/null 2>&1; then
        echo "Unable to queue cleanup with at; falling back to detached cleanup"
        nohup setsid bash -c "$(printf '%s\n%s' "sleep 120" "$cleanup_script")" >/dev/null 2>&1 &
        return 0
    else
        echo "Unable to queue cleanup with at; falling back to background cleanup"
        bash -c "$(printf '%s\n%s' "sleep 120" "$cleanup_script")" >/dev/null 2>&1 &
        return 0
    fi
}

export JOBID=$(squeue -h --name=${ALLOC_NAME} --format=%A)
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
    CLEANUP_CI_BUILDS_DIR="${CUSTOM_CI_BUILDS_DIR/#\$HOME/$HOME}"
    CLEANUP_LOCK_DIR="${CLEANUP_CI_BUILDS_DIR}.cleanup.lock"
    if mkdir "$CLEANUP_LOCK_DIR" 2>/dev/null; then
        schedule_delayed_cleanup || rmdir "$CLEANUP_LOCK_DIR" 2>/dev/null || true
    else
        echo "Delayed cleanup already scheduled for $CLEANUP_CI_BUILDS_DIR"
    fi
fi
