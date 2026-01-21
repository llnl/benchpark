# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.chai.package import Chai as BuiltinChai


class Chai(BuiltinChai):
    variant("single_memory", default=False, description="Enable single memory space model")

    conflicts("+single_memory", when="~rocm")

    version(
        "2025.12.0",
        tag="v2025.12.0",
        commit="26d5646707e1848b0524379b12a7716e4a830a27",
        submodules=False,
    )
    
    def initconfig_hardware_entries(self):
        spec = self.spec
        entries = super().initconfig_hardware_entries()

        if spec.satisfies("+single_memory"):
            entries.append(cmake_cache_option("CHAI_THIN_GPU_ALLOCATE", True))
            entries.append(cmake_cache_option("CHAI_DISABLE_RM", True))

        return entries

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")
