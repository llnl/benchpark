# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.lammps.package import Lammps as BuiltinLammps


class Lammps(BuiltinLammps):

  # commit for FCR
  version("20251219", commit="a51f9ba0e719be544293987bb3cbd9939f1b01ee")

  variant("apu", default=False, description="Enable APU support", when="@4.5: +rocm")

  depends_on("kokkos@5.0.0:", when="@20251219: +kokkos")
  depends_on("kokkos+openmp", when="+openmp")
  depends_on("kokkos+wrapper", when="+cuda")
  depends_on("kokkos+apu", when="+apu")

  def flag_handler(self, name, flags):
    wrapper_flags, x, build_system_flags = super().flag_handler(name, flags)

    if self.spec.satisfies("+apu"):
      if name == "cxxflags":
        build_system_flags.append("-fdenormal-fp-math=ieee")
        build_system_flags.append("-fgpu-flush-denormals-to-zero")

    return (wrapper_flags, x, build_system_flags)

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

    if self.spec.satisfies("+ml-pace"):
        args.append(f"-DPKG_ML-PACE=ON")

    if self.spec.satisfies("+apu"):
      existing_ldflags = self.spec.compiler_flags.get("ldflags", [])
      existing = " ".join(existing_ldflags)
      extra = " -lxpmem -lhugetlbfs"
      if existing:
        combined = f"{existing} {extra}"
      else:
        combined = extra
      args.append(f"-DCMAKE_EXE_LINKER_FLAGS={combined}")

    return args
 
  def install(self, spec, prefix):
    super().install(spec, prefix)
    mkdirp(prefix.src)
    install_tree(self.stage.source_path, prefix.src)
