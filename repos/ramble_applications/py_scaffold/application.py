# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import yaml
from ramble.appkit import *


class PyScaffold(ExecutableApplication):
    """Scale-Free Fractal benchmark - A scalable deep learning benchmark: UNet trained on procedurally-generated, 3D fractal data"""

    name = "scaffold"

    tags = ["python"]

    with when("package_manager_family=pip"):
        software_spec("scaffold", pkg_spec="py-scaffold")

    input_file(
        "config_file",
        url="{config_url}",
        expand=False,
        description="",
    )

    executable(
        "modules",
        'export MPICH_GPU_SUPPORT_ENABLED=0\nexport LD_PRELOAD="/opt/rocm-7.1.1/llvm/lib/libomp.so /opt/cray/pe/mpich/9.1.0/ofi/gnu/11.2/lib/libmpi_gnu.so.12 /collab/usr/gapps/python/toss_4_x86_64_ib/anaconda3-2023.09/lib/libstdc++.so.6"',
    )
    executable(
        "generate",
        "$(which scaffold) generate_fractals -c {config_file} --problem-scale {problem_scale}",
        use_mpi=False,
    )
    executable(
        "run",
        "$(which scaffold) benchmark -c {config_file} --problem-scale {problem_scale} --epochs {num_epochs} --fract-base-dir ../fractals",
        use_mpi=True,
    )

    workload("sweep", executables=["modules", "generate", "run"], input="config_file")
