# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack.pkg.builtin.lammps import Lammps as BuiltinLammps


class Lammps(BuiltinLammps):

  depends_on("kokkos+openmp", when="+openmp")
  depends_on("kokkos+rocm", when="+rocm")
  depends_on("kokkos+cuda", when="+cuda")

  conflicts("+rocm", when="+cuda")
  conflicts("+cuda", when="+rocm")

  def setup_run_environment(self, env):
    super().setup_run_environment(env)

    if self.compiler.extra_rpaths:
      for rpath in self.compiler.extra_rpaths:
        env.prepend_path("LD_LIBRARY_PATH", rpath)

  def setup_build_environment(self, env):
    super().setup_build_environment(env)

    if "+cuda" in self.spec:
      env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

  def cmake_args(self):
    args = super().cmake_args()
    args.append(f"-DMPI_CXX_LINK_FLAGS='{self.spec['mpi'].libs.ld_flags}'")

    cflags = self.spec.compiler_flags['cflags']
    args.append(f"-DCMAKE_C_FLAGS={' '.join(cflags)}")

    cxxflags = self.spec.compiler_flags['cxxflags']
    args.append(f"-DCMAKE_CXX_FLAGS={' '.join(cxxflags)}")

    return args
