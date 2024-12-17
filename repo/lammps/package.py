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
