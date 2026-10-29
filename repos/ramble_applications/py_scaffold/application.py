# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import yaml
from ramble.appkit import *


class PyScaffold(ExecutableApplication):
    """Scale-Free Fractal benchmark - A scalable deep learning benchmark: UNet trained on procedurally-generated, 3D fractal data"""

    name = "py-scaffold"

    tags("python",'ai','ai-training','unet','pytorch','low-precision',
         'ats-6','mpi','nccl','rccl','network-collectives',
         'large-scale','weak-scaling','strong-scaling',
         'llnl-nightly','llnl-monthly','llnl-pr','llnl-weekly')

    register_phase(
        "prepend_library_path", pipeline="setup", run_before=["make_experiments"]
    )

    def _prepend_library_path(self, workspace, app_inst=None):
        """Function to prepend to LD_LIBRARY_PATH, can't do in spack because python_platlib points to wrong site-packages dir"""

        app_inst.variables["mods"] = ""
        if "rocm_arch" in app_inst.variables:
            app_inst.variables["mods"] = "\n".join(
                (
                    "export MIOPEN_DEBUG_CONV_DIRECT=0",
                    "export HIP_LAUNCH_BLOCKING=0",
                    "export MPICH_GPU_SUPPORT_ENABLED=0",
                    "export SCAFFOLD_GROUPNORM_TRITON=1",
                    "export SCAFFOLD_CONV_TRITON=1",
                    "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{pip_purelib_path}/torch/lib",
                )
            )
        elif "cuda_arch" in app_inst.variables:
            app_inst.variables["mods"] = "\n".join(
                (
                    "export LD_LIBRARY_PATH="
                    "/collab/usr/gapps/python/toss_4_x86_64_ib/"
                    "anaconda3-2023.09/lib:"
                    "{pip_purelib_path}/nvidia/cudnn/lib:"
                    "{pip_purelib_path}/torch/lib:"
                    "$LD_LIBRARY_PATH",
                    "export SCAFFOLD_GROUPNORM_TRITON=1",
                )
            )
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
        "$(which scaffold) generate_fractals -c {config_file} "
        "--problem-scale {problem_scale} --fract-base-dir {fractals_dir}",
        use_mpi=True,
    )
    executable(
        "run",
        "$(which scaffold) benchmark -c {config_file} "
        "--problem-scale {problem_scale} --epochs {num_epochs} "
        "--local-batch-size {local_batch_size} "
        "--dc-num-shards {sharding} --fract-base-dir {fractals_dir}",
        use_mpi=True,
    )

    workload("sweep", executables=["modules", "generate", "run"], input="config_file")

    workload_variable(
        "fractals_dir",
        default="{experiment_run_dir}/fractals",
        description="Directory generate writes the fractals to and run reads them from",
        workloads=["sweep"],
    )
