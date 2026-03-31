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

    version(
        "2025.12.1",
        tag="v2025.12.1",
        commit="e3c6197dfa8f1c9ac61635c26775c333411bdcd5",
        submodules=True,
    )
    version(
        "2025.12.0",
        tag="v2025.12.0",
        commit="f2ad263e08db89327ceccaa9a6c1e994b6d24e67",
        submodules=True,
    )

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)

        if self.compiler.extra_rpaths:
            for rpath in self.compiler.extra_rpaths:
                env.prepend_path("LD_LIBRARY_PATH", rpath)
