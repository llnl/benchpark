# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.umpire.package import Umpire as BuiltinUmpire


class Umpire(BuiltinUmpire):

    depends_on("fmt@9.1: cxxstd=17", when="@2024.02.0: %oneapi")

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")
