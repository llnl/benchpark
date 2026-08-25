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

    variant(
        "subkernels",
        default=True,
        description="Enable Caliper subkernel regions when Caliper support is enabled",
    )

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

    depends_on("hip-wrapper", when="+rocm")
    git="https://github.com/TauferLab/RAJAPerf.git"

    version('paper_modifications', branch='paper_modifications', submodules=True)

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def cmake_args(self):
        spec = self.spec
        args = []

        if "+rocm" in spec:
            args.append(f"-DCMAKE_HIP_COMPILER={spec['hip-wrapper'].prefix.bin.hipwrapper}")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)

        if self.compiler.extra_rpaths:
            for rpath in self.compiler.extra_rpaths:
                env.prepend_path("LD_LIBRARY_PATH", rpath)

    def initconfig_package_entries(self):
        entries = super().initconfig_package_entries()
        entries.append(
            cmake_cache_option(
                "RAJA_PERFSUITE_USE_CALIPER_SUBKERNEL", "+subkernels" in self.spec
            )
        )
        return entries
