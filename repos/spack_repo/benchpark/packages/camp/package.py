# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.camp.package import Camp as BuiltinCamp


class Camp(BuiltinCamp):

    version(
        "2025.12.0",
        tag="v2025.12.0",
        commit="a8caefa9f4c811b1a114b4ed2c9b681d40f12325",
        submodules=False,
    )

    variant("default_stream", default=False, description="Use default stream")

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def cmake_args(self):
        options = super().cmake_args()
        options.append(self.define_from_variant("CAMP_USE_PLATFORM_DEFAULT_STREAM", "default_stream"))

        return options
