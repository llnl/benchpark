# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.kripke.package import Kripke as BuiltinKripke


class Kripke(BuiltinKripke):

    def setup_run_environment(self, env):
      super().setup_run_environment(env)

      if self.compiler.extra_rpaths:
        for rpath in self.compiler.extra_rpaths:
          env.prepend_path("LD_LIBRARY_PATH", rpath)
