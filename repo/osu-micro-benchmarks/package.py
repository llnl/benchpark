# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack.pkg.builtin.osu_micro_benchmarks import OsuMicroBenchmarks as BuiltinOsu


class OsuMicroBenchmarks(BuiltinOsu, ROCmPackage):

    depends_on("cray-mpich+gtl", when="+rocm")
    
    def configure_args(self):
        args = super().configure_args()
        if self.spec.satisfies("+rocm"):
            args.extend([f"LDFLAGS={self.spec['mpi'].libs.ld_flags}"]) 
        return args
