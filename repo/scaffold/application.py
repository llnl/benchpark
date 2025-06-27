# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import yaml

from ramble.appkit import *


class Scaffold(ExecutableApplication):
    """Scaffold benchmark"""

    name = "scaffold"

    tags = ["python"]

    register_phase("prepend_library_path", pipeline="setup", run_before=["make_experiments"])

    def _prepend_library_path(self, workspace, app_inst=None):
        """Function to prepend to LD_LIBRARY_PATH, since we are not using Spack"""
        paths = []
        dic = yaml.safe_load(workspace._auxiliary_software_files['compilers.yaml'])
        compilers = dic["compilers"]
        for compiler in compilers:
            env = compiler["compiler"]["environment"]
            if env != {}:
                paths.append(env["prepend_path"]["LD_LIBRARY_PATH"])
        app_inst.variables["ld_paths"] = ":".join(paths)

    os.system("ml load rocm/6.2.1 rocmcc/6.2.1-cce-18.0.1a-magic")
    software_spec("scaffold", None)

    executable(
        "modules",
        "export LD_LIBRARY_PATH={ld_paths}:$LD_LIBRARY_PATH",
    )
    executable(
        "run",
        "SCAFFOLD_REPO_ROOT={package_path} scaffold benchmark -c {package_path}ScaFFold/configs/benchmark_default.yml --parent -j --training-nodes-time 660 --num-ranks {n_gpus} --training-nodes {n_nodes} --n-categories {n_categories}",
    )

    workload("sweep", executables=["modules", "run"])
