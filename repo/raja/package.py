# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack.pkg.builtin.raja import Raja as BuiltinRaja


class Raja(BuiltinRaja):

    version("2025.03.2", tag="v2025.03.2", submodules="True")

    #depends_on("camp+cuda@2025.03.0", when="@2025.03.2:")

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")
