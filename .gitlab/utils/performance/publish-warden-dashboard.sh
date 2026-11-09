#!/bin/bash

set -euo pipefail

# The Plotly Cloud app name and API key are stored as GitLab CI/CD variables.
if [[ -z "${PLOTLY_API_KEY:-}" ]]; then
    echo "Set PLOTLY_API_KEY to publish with the Plotly Cloud CLI." >&2
    exit 1
fi

if [[ -z "${PLOTLY_CLOUD_APP_NAME:-}" ]]; then
    echo "Set PLOTLY_CLOUD_APP_NAME to the Plotly Cloud app name." >&2
    exit 1
fi

# WARDEN currently owns the dashboard app source and the Plotly Cloud bundle
# builder. These values are fixed here so CI has one predictable publish path.
warden_repo_url="https://github.com/llnl/warden.git"
warden_build_output_dir="plotly-cloud-files"

# Dash Mantine Components 3 expects React 19, so tell Dash which browser React
# bundle to serve when the app starts on Plotly Cloud.
react_version="19.2.4"

plotly_venv=""
work_root=""
staged_app_root=""

# Everything created by this script lives in temporary directories. Remove
# them on both success and failure so scheduled CI jobs do not accumulate
# stale WARDEN checkouts or virtual environments.
cleanup() {
    if [[ -n "${plotly_venv}" ]]; then
        rm -rf "${plotly_venv}"
    fi
    if [[ -n "${work_root}" ]]; then
        rm -rf "${work_root}"
    fi
    if [[ -n "${staged_app_root}" ]]; then
        rm -rf "${staged_app_root}"
    fi
}
trap cleanup EXIT

work_root="$(mktemp -d)"
warden_dir="${work_root}/warden"

# Start from a fresh WARDEN checkout every run so the published dashboard reflects
# the current upstream dashboard code and generated app layout.
echo "Cloning WARDEN dashboard source from ${warden_repo_url}."
git clone "${warden_repo_url}" "${warden_dir}"

# Update WARDEN dashboard with latest performance data before building the
# Plotly Cloud upload directory. The command is expected to be available in the
# CI environment.
echo "Updating WARDEN dashboard app files."
(
    cd "${warden_dir}"
    warden_init_or_update
)

# Create the self-contained directory that the Plotly Cloud CLI will publish.
echo "Building WARDEN Plotly Cloud upload files."
(
    cd "${warden_dir}"
    python3 scripts/build_plotly_cloud_files.py --output "${warden_build_output_dir}"
)

generated_app_dir="${warden_dir}/${warden_build_output_dir}"
if [[ ! -d "${generated_app_dir}" ]]; then
    echo "WARDEN Plotly Cloud build did not create expected directory: ${generated_app_dir}" >&2
    exit 1
fi

# Stage a disposable copy of the generated app for publishing.
staged_app_root="$(mktemp -d)"
staged_app_dir="${staged_app_root}/app"
mkdir -p "${staged_app_dir}"
cp -R "${generated_app_dir}/." "${staged_app_dir}"

# Use an existing Plotly Cloud CLI when the runner has one; otherwise install the
# CLI from dash[cloud] into an isolated temporary virtual environment.
plotly_cli="plotly"
if ! command -v "${plotly_cli}" >/dev/null 2>&1; then
    echo "Installing Plotly Cloud CLI in a temporary virtual environment."
    plotly_venv="$(mktemp -d)"
    python3 -m venv "${plotly_venv}"
    "${plotly_venv}/bin/python" -m pip install --upgrade pip
    "${plotly_venv}/bin/python" -m pip install "dash[cloud]"
    plotly_cli="${plotly_venv}/bin/plotly"
fi

# Publish by app name. PLOTLY_API_KEY authenticates the CLI, while REACT_VERSION
# tells Dash which React bundle to serve when the app starts on Plotly Cloud.
echo "Publishing WARDEN dashboard to Plotly Cloud app ${PLOTLY_CLOUD_APP_NAME}."
(
    cd "${staged_app_dir}"
    PLOTLY_API_KEY="${PLOTLY_API_KEY}" \
        REACT_VERSION="${react_version}" \
        "${plotly_cli}" app publish --name "${PLOTLY_CLOUD_APP_NAME}"
)
echo "WARDEN Plotly Cloud publish complete."
