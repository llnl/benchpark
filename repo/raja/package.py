# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.raja.package import Raja as BuiltinRaja


class Raja(BuiltinRaja):

    version(
        "2025.12.1",
        tag="v2025.12.1",
        commit="3b8b59a1e9be2e1066c0d77372b3bf5956e6d6e2",
        submodules=False,
    )
    version(
        "2025.12.0",
        tag="v2025.12.0",
        commit="e827035c630e71a9358e2f21c2f3cf6fd5fb6605",
        submodules=False,
    )
    
    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")
