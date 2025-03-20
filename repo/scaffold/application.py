# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.appkit import *


class Scaffold(ExecutableApplication):
    """Scaffold benchmark"""

    name = "scaffold"

    tags = ["python"]

    executable("req", "pip install -r requirements.txt")
    executable("setup", "python fractal_gen.py --config configs/sweep_default.yml")
    executable("run", "python sweep.py --config configs/sweep_default.yml")

    workload("sweep", executables=["req", "setup", "run"])
