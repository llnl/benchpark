# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack.pkg.builtin.lammps import Lammps as BuiltinLammps


class Lammps(BuiltinLammps):

  version("stable_29Aug2024_update3", tag="stable_29Aug2024_update3")

  depends_on("kokkos+openmp cxxstd=17", when="+openmp")
  depends_on("kokkos+rocm", when="+rocm")
  depends_on("kokkos+cuda cxxstd=17", when="+cuda")
  
  conflicts("+rocm", when="+cuda")
  conflicts("+cuda", when="+rocm")

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

  def cmake_args(self):
    args = super().cmake_args()
    args.append(f"-DMPI_CXX_LINK_FLAGS='{self.spec['mpi'].libs.ld_flags}'")
    args.append(f"-DMPI_C_COMPILER='{self.spec['mpi'].mpicc}'")
    args.append(f"-DMPI_CXX_COMPILER={self.spec['mpi'].mpicxx}")

    return args
 
  def install(self, spec, prefix):
    super().install(spec, prefix)
    mkdirp(prefix.src)
    install_tree(self.stage.source_path, prefix.src)
