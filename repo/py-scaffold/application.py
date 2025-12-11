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

    register_phase("prepend_library_path", pipeline="setup", run_before=["make_experiments"])

    def _prepend_library_path(self, workspace, app_inst=None):
        """Function to prepend to LD_LIBRARY_PATH, can't do in spack because python_platlib points to wrong site-packages dir"""
        paths = []
        # if cuda
        if "cuda_arch" in app_inst.variables.keys():
            # Avoid libcudnn_graph.so error (unnecessary if cuX_full, necessary if cuX wheel)
            paths.append("{pip_site_packages_path}/nvidia/cudnn/lib")

        app_inst.variables["rocm_mods"] = ""
        if "rocm_arch" in app_inst.variables.keys():
            app_inst.variables["rocm_mods"] = "pip install amdsmi==6.4.0\nmodule load rocm/6.4.2 rccl/fast-env-slows-mpi\nexport MPICH_GPU_SUPPORT_ENABLED=0\nexport LD_LIBRARY_PATH=/collab/usr/global/tools/rccl/toss_4_x86_64_ib_cray/rocm-6.4.1/install/lib/:$LD_LIBRARY_PATH\export LD_LIBRARY_PATH=/opt/cray/pe/cce/20.0.0/cce/x86_64/lib:$LD_LIBRARY_PATH\n"

        # if caliper - Avoid libcaffe2_nvrtc.so
        paths.append("{pip_site_packages_path}/torch/lib")

        app_inst.variables["ld_paths"] = ":".join(paths)

    software_spec("scaffold", None)

    # TODO: Figure out MPICH_GPU_SUPPORT_ENABLED=0, disabling GTL otherwise linker error.
    executable(
        "modules",
        "{rocm_mods}export LD_LIBRARY_PATH={ld_paths}:$LD_LIBRARY_PATH",
    )
    executable(
        "generate",
        "scaffold generate_fractals -c {package_path}ScaFFold/configs/benchmark_default.yml --problem-scale {problem_scale}",
        use_mpi=True,
    )
    executable(
        "run",
        "scaffold benchmark -c {package_path}ScaFFold/configs/benchmark_default.yml --problem-scale {problem_scale}",
        use_mpi=True,
    )

    workload("sweep", executables=["modules", "generate", "run"])
