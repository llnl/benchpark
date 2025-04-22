# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from ramble.appkit import *


class Scaffold(ExecutableApplication):
    """Scaffold benchmark"""

    name = "scaffold"

    tags = ["python"]

    os.system("ml load rocm/6.2.1 rocmcc/6.2.1-cce-18.0.1a-magic")
    software_spec("scaffold", None)

    executable(
        "modules",
        "export LD_LIBRARY_PATH=/opt/cray/pe/cce/18.0.1/cce/x86_64/lib:$LD_LIBRARY_PATH",
    )
    executable(
        "run",
        "SCAFFOLD_REPO_ROOT={package_path} scaffold benchmark --parent --config {package_path}ScaFFold/configs/{config}.yml -j",
    )

    workload("sweep", executables=["modules", "run"])
