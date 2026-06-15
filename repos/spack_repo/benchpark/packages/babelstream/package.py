# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *

from spack_repo.builtin.packages.babelstream.package import CMakeBuilder as BabelstreamCMakeBuilder
from spack_repo.builtin.packages.babelstream.package import Babelstream as BuiltinBabelstream

class Babelstream(BuiltinBabelstream):
    git = "https://github.com/rfhaque/BabelStream.git"

    version("main", branch="fix_adiak_variable")

    variant("caliper", default=False, description="Enable/disable Caliper support")

    #caliper dependency
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")

    def setup_run_environment(self, env):
      if self.compiler.extra_rpaths:
        for rpath in self.compiler.extra_rpaths:
          env.prepend_path("LD_LIBRARY_PATH", rpath)

class CMakeBuilder(BabelstreamCMakeBuilder):
    def cmake_args(self):
        args = super().cmake_args()
        #enable caliper
        if "+caliper" in self.spec:
            args.append(self.define_from_variant("ENABLE_CALIPER", "caliper"))
        return args
