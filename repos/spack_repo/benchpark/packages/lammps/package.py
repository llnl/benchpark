# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.lammps.package import Lammps as BuiltinLammps


class Lammps(BuiltinLammps):

  variant("pace", default=False, description="Enable the ML PACE module")
  depends_on("pace", when="+pace")

  depends_on("kokkos+openmp cxxstd=17", when="+openmp")
  depends_on("kokkos+wrapper", when="+cuda")

  # Kokkos 5 not building
  depends_on("kokkos@:4", when="@:20250722 +kokkos")
  
  flag_handler = build_system_flags

  def setup_run_environment(self, env):
    super().setup_run_environment(env)

    if self.compiler.extra_rpaths:
      for rpath in self.compiler.extra_rpaths:
        env.prepend_path("LD_LIBRARY_PATH", rpath)

  def setup_build_environment(self, env):
    super().setup_build_environment(env)

    if "+cuda" in self.spec:
      env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

      if "+mpi" in self.spec:
          if self.spec["mpi"].extra_attributes and "ldflags" in self.spec["mpi"].extra_attributes:
              env.append_flags("LDFLAGS", self.spec["mpi"].extra_attributes["ldflags"])

  def cmake_args(self):
    args = super().cmake_args()
    args.append(f"-DMPI_CXX_LINK_FLAGS='{self.spec['mpi'].libs.ld_flags}'")
    args.append(f"-DMPI_C_COMPILER='{self.spec['mpi'].mpicc}'")
    args.append(f"-DMPI_CXX_COMPILER={self.spec['mpi'].mpicxx}")
    if "+pace" in self.spec:
        args.append(f"-DPKG_ML-PACE=ON")

    return args
 
  def install(self, spec, prefix):
    super().install(spec, prefix)
    mkdirp(prefix.src)
    install_tree(self.stage.source_path, prefix.src)
