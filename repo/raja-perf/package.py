# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from os import environ as env

from spack.package import *
from spack_repo.builtin.packages.raja_perf.package import RajaPerf as BuiltinRajaPerf


class RajaPerf(BuiltinRajaPerf, CachedCMakePackage, CudaPackage, ROCmPackage):
    """RAJA Performance Suite."""

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)

        if self.compiler.extra_rpaths:
            for rpath in self.compiler.extra_rpaths:
                env.prepend_path("LD_LIBRARY_PATH", rpath)
