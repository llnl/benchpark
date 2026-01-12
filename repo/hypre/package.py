# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
from itertools import product

from spack.package import *
from spack_repo.builtin.build_systems.rocm import ROCmPackage
from spack_repo.builtin.packages.hypre.package import (
    AutotoolsBuilder as HypreAutotoolsBuilder,
)
from spack_repo.builtin.packages.hypre.package import CMakeBuilder as HypreCMakeBuilder
from spack_repo.builtin.packages.hypre.package import Hypre as BuiltinHypre


class Hypre(BuiltinHypre):
    requires("+rocm", when="^rocblas")
    requires("+rocm", when="^rocsolver")

    with when("+cuda"):
        for pkg, sm_ in product(["umpire", "magma"], CudaPackage.cuda_arch_values):
            depends_on(f"{pkg} cuda_arch={sm_}", when=f"+{pkg} cuda_arch={sm_}")

    with when("+rocm"):
        for pkg, gfx in product(["umpire", "magma"], ROCmPackage.amdgpu_targets):
            depends_on(f"{pkg} amdgpu_target={gfx}", when=f"+{pkg} amdgpu_target={gfx}")

    compiler_to_cpe_name = {
        "cce": "cray",
        "gcc": "gnu",
    }

    def setup_build_environment(self, env):
        if self.spec.satisfies('%oneapi'):
            compiler_version = self.spec.compiler.version

            # Convert to integer for comparison (e.g., 2023.1.0 -> 2023)
            major_version = int(str(compiler_version).split('.')[0])

            if major_version < 2023:
                raise RuntimeError(
                    "This package requires Intel oneAPI compiler version 2023 or newer. "
                    "Detected version: {0}".format(compiler_version)
                )

        super().setup_build_environment(env)

        spec = self.spec
        if "+mpi" in spec:
            if "+fortran" in spec:
                env.set("FC", spec["mpi"].mpifc)
            if spec["mpi"].extra_attributes and "ldflags" in spec["mpi"].extra_attributes:
                env.append_flags("LDFLAGS", spec["mpi"].extra_attributes["ldflags"])
        if spec["lapack"].satisfies("rocsolver"):
            rocm_rpath_flag = f"-Wl,-rpath,{os.path.dirname(spec['lapack'].prefix)}/lib"
            env.append_flags("LDFLAGS", rocm_rpath_flag)
        if spec["lapack"].satisfies("cray-libsci"):
            libsci_name = "sci_"
            libsci_name += self.compiler_to_cpe_name[spec.compiler.name]
            if spec.satisfies("+mpi"):
                libsci_name += "_mpi"
            if spec.satisfies("+openmp"):
                libsci_name += "_mp"
            env.append_flags("LDFLAGS", f"-L{spec['lapack'].prefix}/lib -l{libsci_name}")
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

class CMakeBuilder(HypreCMakeBuilder):
    pass

class AutotoolsBuilder(HypreAutotoolsBuilder):
    pass
