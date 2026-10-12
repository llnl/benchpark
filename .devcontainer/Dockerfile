# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

# Tracks the latest Ubuntu 26.04.x point release
FROM mcr.microsoft.com/devcontainers/base:ubuntu26.04

# pyproject.toml requires python>=3.8 and black targets up to py311
ARG PYTHON_VERSION=3.11
ARG CMAKE_VERSION=4.4.4

# System prerequisites for Spack and Ramble
RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
        build-essential \
        bzip2 \
        ca-certificates \
        curl \
        file \
        gfortran \
        git \
        gnupg2 \
        patch \
        unzip \
        xz-utils \
        zstd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ubuntu 26.04 does not package the pinned Python, so install it with uv.
# The /usr/local/bin/python3 link gives the VS Code Python Environments
# extension a "global" Python; without one it prompts to install Python via uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_PYTHON_INSTALL_DIR=/opt/python \
    VIRTUAL_ENV=/opt/venv
RUN uv python install "${PYTHON_VERSION}" \
    && ln -s "$(uv python find --system "${PYTHON_VERSION}")" /usr/local/bin/python3 \
    && uv venv --seed --python "${PYTHON_VERSION}" "${VIRTUAL_ENV}" \
    && chown -R vscode:vscode "${VIRTUAL_ENV}"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

USER vscode

# Recent CMake (from PyPI, which ships multi-arch binary wheels)
RUN pip install --no-cache-dir "cmake==${CMAKE_VERSION}"

# Python dependencies for Benchpark and Ramble
COPY --chown=vscode:vscode requirements.txt /tmp/benchpark/requirements.txt
RUN pip install --no-cache-dir -r /tmp/benchpark/requirements.txt

# Pre-clone Ramble, Spack, and spack-packages at the commits pinned in
# checkout-versions.yaml, into the default bootstrap location from
# config/bootstrap.yaml (~/.benchpark/), so benchpark does not need to fetch them.
COPY --chown=vscode:vscode checkout-versions.yaml remote-urls.yaml /tmp/benchpark/
RUN set -eu; \
    cd /tmp/benchpark; \
    for repo in ramble spack spack-packages; do \
        commit=$(awk -v k="${repo}:" '$1 == k {print $2}' checkout-versions.yaml); \
        url=$(awk -v k="${repo}:" '$1 == k {print $2}' remote-urls.yaml); \
        dest="${HOME}/.benchpark/${repo}"; \
        mkdir -p "${dest}"; \
        git -C "${dest}" init -q; \
        git -C "${dest}" remote add origin "${url}"; \
        git -C "${dest}" fetch -q --depth 1 origin "${commit}"; \
        git -C "${dest}" checkout -q FETCH_HEAD; \
    done

ENV PATH="/home/vscode/.benchpark/spack/bin:/home/vscode/.benchpark/ramble/bin:${PATH}"
