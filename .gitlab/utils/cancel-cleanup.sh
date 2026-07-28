#!/bin/bash

set -u

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <ci-builds-dir>" >&2
    exit 1
fi

CLEANUP_CI_BUILDS_DIR="${1/#\$HOME/$HOME}"
CLEANUP_LOCK_DIR="${CLEANUP_CI_BUILDS_DIR}.cleanup.lock"

# On pipeline cancellation, Jacamar can recreate runner temp directories after the
# job's after_script runs. Delay cleanup until after the runner lifecycle finishes.
schedule_delayed_cleanup() {
    cleanup_script=$(printf '%s\n' \
        "lock=$(printf "%q" "$CLEANUP_LOCK_DIR")" \
        "target=$(printf "%q" "$CLEANUP_CI_BUILDS_DIR")" \
        'rm -rf "$target"' \
        'rmdir "$lock" || true')

    echo "Scheduling delayed cleanup for $CLEANUP_CI_BUILDS_DIR"
    if command -v at >/dev/null 2>&1 &&
        printf '%s\n' "$cleanup_script" | at now + 5 minutes >/dev/null 2>&1; then
        echo "Delayed cleanup queued with at"
        return 0
    fi

    echo "Unable to queue delayed cleanup with at" >&2
    return 1
}

if mkdir "$CLEANUP_LOCK_DIR" 2>/dev/null; then
    schedule_delayed_cleanup || rmdir "$CLEANUP_LOCK_DIR" 2>/dev/null || true
else
    echo "Delayed cleanup already scheduled for $CLEANUP_CI_BUILDS_DIR"
fi
