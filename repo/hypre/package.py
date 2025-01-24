# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from spack.package import *
from spack.pkg.builtin.hypre import Hypre as BuiltinHypre


class Hypre(BuiltinHypre):
    requires("+rocm", when="^rocblas")
    requires("+rocm", when="^rocsolver")

    compiler_to_cpe_name = {
        "cce": "cray",
        "gcc": "gnu",
    }

    def configure_args(self):
        configure_args = super().configure_args()

        if (self.compiler.fc and 'xlf' in self.compiler.fc) or (self.compiler.f77 and 'xlf' in self.compiler.f77):
          if not "+fortran" in self.spec:        
            configure_args.append("--with-fmangle=no-underscores")
            configure_args.append("--with-fmangle-blas=no-underscores") 
            configure_args.append("--with-fmangle-lapack=no-underscores")

        if self.spec["blas"].satisfies("rocblas"):
            configure_args.append("--enable-rocblas")
        if self.spec.satisfies("^cray-mpich+gtl"):
            configure_args.append("--enable-gpu-aware-mpi")

        return configure_args

    def setup_build_environment(self, env):
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
