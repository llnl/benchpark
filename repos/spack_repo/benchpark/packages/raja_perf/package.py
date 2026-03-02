# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from os import environ as env

from spack.package import *
from spack_repo.builtin.build_systems.cached_cmake import (
    CachedCMakePackage,
    cmake_cache_option,
    cmake_cache_path,
    cmake_cache_string,
)
from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage
from spack_repo.builtin.packages.raja_perf.package import RajaPerf as BuiltinRajaPerf


class RajaPerf(BuiltinRajaPerf):
    """RAJA Performance Suite."""

    depends_on("hip-wrapper", when="+rocm")

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def cmake_args(self):
        spec = self.spec
        args = []

        if "+rocm" in spec:
            args.append(f"-DCMAKE_HIP_COMPILER={spec['hip-wrapper'].prefix.bin.hipwrapper}")

        return args
