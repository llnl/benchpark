# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack.pkg.builtin.lammps import Lammps as BuiltinLammps


class Lammps(BuiltinLammps):

  depends_on("kokkos+openmp cxxstd=17", when="+openmp")
  depends_on("kokkos+rocm", when="+rocm")
  depends_on("kokkos@4.3.01 +cuda cxxstd=17", when="+cuda")
  
  def cmake_args(self):
    args=super(BuiltinLammps, self).cmake_args()
    if "+cuda" in self.spec:
        args.append(f"-DKokkos_DIR=%s/lib64/cmake/Kokkos" % self.spec["kokkos"].prefix)
        args.append(f"-DKokkos_ENABLE_CUDA=ON")

    return args

  def setup_run_environment(self, env):

    super(BuiltinLammps, self).setup_run_environment(env)

    if self.compiler.extra_rpaths:
      for rpath in self.compiler.extra_rpaths:
        env.prepend_path("LD_LIBRARY_PATH", rpath)

  def setup_build_environment(self, env):
    super().setup_build_environment(env)

    spec = self.spec
    if "+mpi" in spec:
      if spec["mpi"].extra_attributes and "ldflags" in spec["mpi"].extra_attributes:
        env.append_flags("LDFLAGS", spec["mpi"].extra_attributes["ldflags"])


