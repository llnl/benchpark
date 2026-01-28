# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib

import benchpark.base_paths
import benchpark.config


class Paths:
    def __init__(self, base_paths):
        bootstrap_cfg = benchpark.config.configuration().bootstrap

        self.benchpark_home = pathlib.Path(os.path.expanduser(bootstrap_cfg.location))
        self.global_ramble_path = self.benchpark_home / "ramble"
        self.global_spack_path = self.benchpark_home / "spack"

        self.base_paths = base_paths

    def __getattr__(self, name):
        return getattr(self.base_paths, name)


paths = Paths(benchpark.base_paths.base_paths)
hardware_descriptions = paths.hardware_descriptions
