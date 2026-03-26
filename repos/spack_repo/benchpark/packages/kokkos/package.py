# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.kokkos.package import Kokkos as BuiltinKokkos


class Kokkos(BuiltinKokkos):
  variant(
    "deprecated_code_4",
    default=False,
    when="@5:",
    description="Whether to enable deprecated code in Kokkos 4",
  )

  def setup_build_environment(self, env):
    if "+cuda" in self.spec:
      env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

  def cmake_args(self):
    options = [opt for opt in super().cmake_args()]
    if self.spec.satisfies("+deprecated_code_4"):
      options.append(
        self.define_from_variant("Kokkos_ENABLE_DEPRECATED_CODE_4", "deprecated_code_4")
      )

    return options 
