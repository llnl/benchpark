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

    register_phase(
        "prepend_library_path", pipeline="setup", run_before=["make_experiments"]
    )

    def _prepend_library_path(self, workspace, app_inst=None):
        """Function to prepend to LD_LIBRARY_PATH, can't do in spack because python_platlib points to wrong site-packages dir"""

        app_inst.variables["mods"] = ""
        if "rocm_arch" in app_inst.variables.keys():
            app_inst.variables["mods"] = (
                'export MIOPEN_DEBUG_CONV_DIRECT=0\nexport HIP_LAUNCH_BLOCKING=0\nexport MPICH_GPU_SUPPORT_ENABLED=0\nexport LD_PRELOAD="/opt/intel/oneapi/mkl/2024.2/lib/libmkl_core.so.2 /opt/intel/oneapi/mkl/2024.2/lib/libmkl_gnu_thread.so.2 /opt/intel/oneapi/mkl/2024.2/lib/libmkl_intel_lp64.so.2 /opt/rocm-7.1.1/llvm/lib/libomp.so /opt/cray/pe/mpich/9.1.0/ofi/gnu/11.2/lib/libmpi_gnu.so.12 /collab/usr/gapps/python/toss_4_x86_64_ib/anaconda3-2023.09/lib/libstdc++.so.6"\nexport LD_LIBRARY_PATH="/opt/intel/oneapi/mkl/2024.2/lib:$LD_LIBRARY_PATH"'
            )
        elif "cuda_arch" in app_inst.variables.keys():
            app_inst.variables["mods"] = 'export LD_LIBRARY_PATH=/collab/usr/gapps/python/toss_4_x86_64_ib/anaconda3-2023.09/lib:{pip_purelib_path}/nvidia/cudnn/lib:{pip_purelib_path}/torch/lib:$LD_LIBRARY_PATH'
        else:
            app_inst.variables["mods"] = ":"

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
        "{mods}",
    )
    executable(
        "generate",
        "$(which scaffold) generate_fractals -c {config_file} --problem-scale {problem_scale}",
        use_mpi=False,
    )
    executable(
        "run",
        "$(which scaffold) benchmark -c {config_file} --problem-scale {problem_scale} --epochs {num_epochs}",
        use_mpi=True,
    )

    workload("sweep", executables=["modules", "generate", "run"], input="config_file")
