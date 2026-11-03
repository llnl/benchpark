#!/bin/bash
set -euo pipefail

if [[ -z "${PLOTLY_CLOUD_REDEPLOY_WEBHOOK:-}" ]]; then
    echo "PLOTLY_CLOUD_REDEPLOY_WEBHOOK must contain the Plotly Cloud redeploy webhook URL." >&2
    exit 1
fi

echo "Triggering WARDEN Plotly Cloud redeploy."
curl -fsS -X POST "${PLOTLY_CLOUD_REDEPLOY_WEBHOOK}"
echo
echo "WARDEN Plotly Cloud redeploy requested."
