#!/bin/bash
set -euo pipefail

plotly_api_key="${PLOTLY_API_KEY:-${PLOTLY_CLOUD_API_KEY:-}}"
if [[ -z "${plotly_api_key}" ]]; then
    echo "Set PLOTLY_API_KEY or PLOTLY_CLOUD_API_KEY to publish with the Plotly Cloud CLI." >&2
    exit 1
fi

python="${PYTHON:-python3}"
plotly_cli="${PLOTLY_CLOUD_CLI:-plotly}"
plotly_react_version="${PLOTLY_CLOUD_REACT_VERSION:-19.2.4}"
dash_requirement_pin="${PLOTLY_CLOUD_DASH_REQUIREMENT_PIN:-dash==4.5.0}"
dmc_requirement_pin="${PLOTLY_CLOUD_DMC_REQUIREMENT_PIN:-dash-mantine-components==3.0.0}"
warden_repo_url="${WARDEN_REPO_URL:-https://github.com/llnl/warden.git}"
warden_update_cmd="${WARDEN_INIT_OR_UPDATE_CMD:-warden_init_or_update}"
warden_build_script="${WARDEN_PLOTLY_CLOUD_BUILD_SCRIPT:-scripts/build_plotly_cloud_files.py}"
warden_build_output_dir="${WARDEN_PLOTLY_CLOUD_OUTPUT_DIR:-plotly-cloud-files-v3}"
plotly_venv=""
warden_checkout_root=""
warden_worktree_path=""
staged_app_root=""

cleanup() {
    if [[ -n "${plotly_venv}" ]]; then
        rm -rf "${plotly_venv}"
    fi
    if [[ -n "${warden_checkout_root}" ]]; then
        rm -rf "${warden_checkout_root}"
    fi
    if [[ -n "${staged_app_root}" ]]; then
        rm -rf "${staged_app_root}"
    fi
}
trap cleanup EXIT

resolve_warden_worktree_path() {
    local checkout_parent
    local warden_checkout

    if [[ -n "${WARDEN_CHECKOUT_PATH:-}" ]]; then
        warden_worktree_path="${WARDEN_CHECKOUT_PATH}"
    elif [[ -n "${PLOTLY_CLOUD_APP_PATH:-}" ]]; then
        warden_worktree_path="${PLOTLY_CLOUD_APP_PATH}"
    else
        checkout_parent="$(mktemp -d)"
        warden_checkout_root="${checkout_parent}"
        warden_checkout="${warden_checkout_root}/warden"

        echo "Cloning WARDEN dashboard source from ${warden_repo_url}."
        git clone "${warden_repo_url}" "${warden_checkout}"

        if [[ -n "${WARDEN_REF:-}" ]]; then
            git -C "${warden_checkout}" checkout "${WARDEN_REF}"
        fi

        warden_worktree_path="${warden_checkout}"
    fi

    if [[ ! -d "${warden_worktree_path}" ]]; then
        echo "Missing WARDEN checkout directory: ${warden_worktree_path}" >&2
        exit 1
    fi
}

run_warden_init_or_update() {
    local update_exe

    echo "Updating WARDEN dashboard app files with ${warden_update_cmd}."
    (
        cd "${warden_worktree_path}"

        if command -v "${warden_update_cmd}" >/dev/null 2>&1; then
            update_exe="$(command -v "${warden_update_cmd}")"
        elif [[ -x "./${warden_update_cmd}" ]]; then
            update_exe="./${warden_update_cmd}"
        elif [[ -x "./bin/${warden_update_cmd}" ]]; then
            update_exe="./bin/${warden_update_cmd}"
        elif [[ -x "./scripts/${warden_update_cmd}" ]]; then
            update_exe="./scripts/${warden_update_cmd}"
        else
            echo "Cannot find executable ${warden_update_cmd} in PATH, WARDEN root, bin/, or scripts/." >&2
            exit 1
        fi

        "${update_exe}"
    )
}

build_plotly_cloud_files() {
    local build_script_path
    local output_path

    build_script_path="${warden_build_script}"
    if [[ "${build_script_path}" != /* ]]; then
        build_script_path="${warden_worktree_path}/${build_script_path}"
    fi

    if [[ ! -f "${build_script_path}" ]]; then
        echo "Missing WARDEN Plotly Cloud build script: ${build_script_path}" >&2
        exit 1
    fi

    echo "Building WARDEN Plotly Cloud upload files with ${build_script_path}."
    (
        cd "${warden_worktree_path}"
        "${python}" "${build_script_path}" --output "${warden_build_output_dir}"
    )

    if [[ "${warden_build_output_dir}" == /* ]]; then
        output_path="${warden_build_output_dir}"
    else
        output_path="${warden_worktree_path}/${warden_build_output_dir}"
    fi

    if [[ ! -d "${output_path}" ]]; then
        echo "WARDEN Plotly Cloud build did not create expected directory: ${output_path}" >&2
        exit 1
    fi

    app_path="${output_path}"
}

stage_app() {
    local source_app_path=$1
    local requirements_file
    local pinned_requirements

    staged_app_root="$(mktemp -d)"
    mkdir -p "${staged_app_root}/app"
    cp -R "${source_app_path}/." "${staged_app_root}/app"

    requirements_file="${staged_app_root}/app/requirements.txt"
    if [[ ! -f "${requirements_file}" ]]; then
        touch "${requirements_file}"
    fi

    pinned_requirements="$(mktemp)"
    awk '
        function canonical_name(line) {
            sub(/[;#].*/, "", line)
            sub(/^[[:space:]]+/, "", line)
            sub(/\[.*/, "", line)
            split(line, parts, /[[:space:]<>=!~]/)
            name = tolower(parts[1])
            gsub(/_/, "-", name)
            return name
        }
        {
            name = canonical_name($0)
            if (name == "dash" || name == "dash-mantine-components") {
                next
            }
            print
        }
    ' "${requirements_file}" > "${pinned_requirements}"
    {
        printf '\n# Pinned by Benchpark dashboard publish to keep DMC and React compatible.\n'
        printf '%s\n' "${dash_requirement_pin}"
        printf '%s\n' "${dmc_requirement_pin}"
    } >> "${pinned_requirements}"
    mv "${pinned_requirements}" "${requirements_file}"

    app_path="${staged_app_root}/app"
}

resolve_warden_worktree_path
run_warden_init_or_update
build_plotly_cloud_files
stage_app "${app_path}"

if ! command -v "${plotly_cli}" >/dev/null 2>&1; then
    if [[ "${PLOTLY_CLOUD_INSTALL_CLI:-1}" != "1" ]]; then
        echo "Plotly Cloud CLI not found. Install dash[cloud], set PLOTLY_CLOUD_CLI, or set PLOTLY_CLOUD_INSTALL_CLI=1." >&2
        exit 1
    fi

    echo "Installing Plotly Cloud CLI in a temporary virtual environment."
    plotly_venv="$(mktemp -d)"
    "${python}" -m venv "${plotly_venv}"
    "${plotly_venv}/bin/python" -m pip install --upgrade pip
    "${plotly_venv}/bin/python" -m pip install "dash[cloud]"
    plotly_cli="${plotly_venv}/bin/plotly"
else
    plotly_cli="$(command -v "${plotly_cli}")"
fi

publish_args=(app publish)

app_config_set=0
if [[ -n "${PLOTLY_CLOUD_APP_CONFIG:-}" ]]; then
    app_config="${PLOTLY_CLOUD_APP_CONFIG}"
    if [[ "${app_config}" != /* ]]; then
        app_config="${PWD}/${app_config}"
    fi
    publish_args+=(--config "${app_config}")
    app_config_set=1
elif [[ -f "${app_path}/plotly-cloud.toml" ]]; then
    app_config_set=1
fi

if [[ -n "${PLOTLY_CLOUD_APP_NAME:-}" ]]; then
    publish_args+=(--name "${PLOTLY_CLOUD_APP_NAME}")
elif [[ "${app_config_set}" != "1" ]]; then
    echo "PLOTLY_CLOUD_APP_NAME is required unless the app directory has plotly-cloud.toml or PLOTLY_CLOUD_APP_CONFIG is set." >&2
    exit 1
fi

if [[ -n "${PLOTLY_CLOUD_TEAM:-}" ]]; then
    publish_args+=(--team "${PLOTLY_CLOUD_TEAM}")
fi

echo "Publishing WARDEN dashboard to Plotly Cloud."
(
    cd "${app_path}"
    PLOTLY_API_KEY="${plotly_api_key}" \
        REACT_VERSION="${plotly_react_version}" \
        "${plotly_cli}" "${publish_args[@]}"
)
echo "WARDEN Plotly Cloud publish complete."
