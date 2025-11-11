# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.osu_micro_benchmarks.package import (
    OsuMicroBenchmarks as BuiltinOsu,
)


class OsuMicroBenchmarks(BuiltinOsu, ROCmPackage):

    depends_on("cray-mpich+gtl", when="+rocm")
    
    def configure_args(self):
        args = super().configure_args()
        if self.spec.satisfies("+rocm"):
            args.extend([f"LDFLAGS={self.spec['mpi'].libs.ld_flags}"]) 
            print(self.spec['mpi'])
        new_args = list()
        for x in args:
            if "NVCCFLAGS" in x and self.spec.satisfies("%intel-oneapi-compilers"):
                new_args.append(x + " -allow-unsupported-compiler")
            else:
                new_args.append(x)
        return new_args

    def setup_run_environment(self, env):
        mpidir = join_path(self.prefix.libexec, "osu-micro-benchmarks", "mpi")
        env.prepend_path("PATH", join_path(mpidir, "startup"))
        env.prepend_path("PATH", join_path(mpidir, "pt2pt"))
        env.prepend_path("PATH", join_path(mpidir, "one-sided"))
        env.prepend_path("PATH", join_path(mpidir, "collective"))
        if self.spec.satisfies("+rocm"):
            if 'gtl_flags' in self.spec['mpi'].extra_attributes:
                env.prepend_path("LOCAL_RANK", self.spec['mpi'].extra_attributes['gtl_flags'])
