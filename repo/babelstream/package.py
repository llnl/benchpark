# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack.pkg.builtin.babelstream import Babelstream as BuiltinBabel
from spack.pkg.builtin.babelstream import CMakeBuilder as BuiltinBuilder


class Babelstream(BuiltinBabel):

    git = "https://github.com/august-knox/BabelStream.git"
    version("caliper", branch="caliper-annotations")

    variant("openmp", default=False, description = "wrapper for omp variant")
    variant("caliper", default=False, description = "Enable caliper performance tracking")
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")
    
class CMakeBuilder(BuiltinBuilder):
    def cmake_args(self):
        args = super().cmake_args()
        #enable caliper
        if "+caliper" in self.spec:
            args.append(self.define_from_variant("ENABLE_CALIPER", "caliper"))
        return args

