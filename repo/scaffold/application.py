# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.appkit import *


class Scaffold(ExecutableApplication):
    """Scaffold benchmark"""

    name = "scaffold"

    tags = ["python"]

    executable(
        "modules",
        "ml load rocm/6.2.1 rocmcc/6.2.1-cce-18.0.1a-magic",
    )
    executable(
        "build",
        "pip install {package_path} --extra-index-url https://download.pytorch.org/whl/rocm6.2",
        output_capture=OUTPUT_CAPTURE.ALL,
    )
    executable(
        "config",
        "scaffold fractal_gen.py --config {package_path}ScaFFold/configs/benchmark_default.yml",
    )
    executable(
        "run",
        "scaffold sweep.py --config {package_path}ScaFFold/configs/benchmark_default.yml",
    )

    workload("sweep", executables=["modules", "build", "config", "run"])
