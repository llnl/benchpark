#!/bin/bash
set -x

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
        'if mkdir "$lock" 2>/dev/null; then' \
        '    echo "Removing $target"' \
        '    rm -rf "$target"' \
        '    rmdir "$lock" 2>/dev/null || true' \
        'else' \
        '    echo "Cleanup already running for $target"' \
        'fi')

    echo "Scheduling delayed cleanup for $CLEANUP_CI_BUILDS_DIR"
    if command -v at >/dev/null 2>&1 &&
        printf '%s\n' "$cleanup_script" | at now + 2 minutes; then
        echo "Delayed cleanup queued with at"
    elif command -v setsid >/dev/null 2>&1; then
        echo "Unable to queue cleanup with at; falling back to detached cleanup"
        nohup setsid bash -c "$(printf '%s\n%s' "sleep 120" "$cleanup_script")" >/dev/null 2>&1 &
    else
        echo "Unable to queue cleanup with at; falling back to background cleanup"
        bash -c "$(printf '%s\n%s' "sleep 120" "$cleanup_script")" >/dev/null 2>&1 &
    fi
}

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
    schedule_delayed_cleanup
fi
