# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack.pkg.builtin.babelstream import Babelstream as BuiltinBabel
from spack.pkg.builtin.babelstream import CMakeBuilder as BuiltinBuilder


class Babelstream(BuiltinBabel):

    git = "https://github.com/august-knox/BabelStream.git"
    version("5.0", tag="v5.0")
    version("4.0", sha256="a9cd39277fb15d977d468435eb9b894f79f468233f0131509aa540ffda4f5953")
    version("main", branch="main")
    version("develop", branch="develop")
    version("caliper", branch="caliper-annotations")

    variant("openmp", default=False, description = "wrapper for omp variant")
    variant("caliper", default=False, description = "Enable caliper performance tracking")
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")

    requires("+omp", when="+openmp")
    requires("~omp", when="~openmp")

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    
class CMakeBuilder(BuiltinBuilder):
    def cmake_args(self):
        args = super().cmake_args()
        #enable caliper
        if "+caliper" in self.spec:
            args.append(self.define_from_variant("ENABLE_CALIPER", "caliper"))
        return args

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")
