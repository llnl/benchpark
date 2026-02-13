# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.kokkos.package import Kokkos as BuiltinKokkos


class Kokkos(BuiltinKokkos):
  flag_handler = build_system_flags

  def setup_build_environment(self, env):
    if "+cuda" in self.spec:
      env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")
