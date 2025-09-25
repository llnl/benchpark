# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import yaml

from ramble.appkit import *


class PyScaffold(ExecutableApplication):
    """Scaffold benchmark"""

    name = "scaffold"

    tags = ["python"]

    register_phase("prepend_library_path", pipeline="setup", run_before=["make_experiments"])

    def _prepend_library_path(self, workspace, app_inst=None):
        """Function to prepend to LD_LIBRARY_PATH, since we are not using Spack"""
        paths = []
        dic = yaml.safe_load(workspace._auxiliary_software_files['compilers.yaml'])
        compilers = list(dic.values())[0]
        for compiler in compilers:
            env = compiler["compiler"]["environment"]
            if env != {}:
                paths.append(env["prepend_path"]["LD_LIBRARY_PATH"])
        app_inst.variables["ld_paths"] = ":".join(paths)

    software_spec("scaffold", None)

    executable(
        "modules",
        "export LD_LIBRARY_PATH={ld_paths}:$LD_LIBRARY_PATH",
    )
    executable(
        "pip",
        "pip install -r {package_path}requirements.txt\npip install torch==2.8.0+rocm6.4 --extra-index-url https://download.pytorch.org/whl/rocm6.4",
        use_mpi=False,
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

    workload("sweep", executables=["modules", "pip",
                                    "generate",
                                    "run"])
