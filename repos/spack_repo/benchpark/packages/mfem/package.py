# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import sys

from spack.package import *
from spack_repo.builtin.packages.mfem.package import Mfem as BuiltinMfem


class Mfem(BuiltinMfem):

    variant("caliper", default=False, description="Build Caliper support")

    depends_on("camp+default_stream", when="+umpire")
    depends_on("camp@main", when="@develop +umpire")
    depends_on("umpire@develop", when="@develop +umpire")

    depends_on("camp+default_stream", when="+raja")
    depends_on("camp@main", when="@develop +raja")
    depends_on("raja@develop cxxstd=20", when="@develop +raja")

    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")
    depends_on("hypre+shared", when="+mpi~cuda")

    requires("+caliper", when="^hypre+caliper")

    def configure(self, spec, prefix):
        if spec.satisfies('%oneapi'):
            spec.compiler_flags["cxxflags"] = [flag for flag in spec.compiler_flags["cxxflags"] if not flag.startswith('-O')]
            spec.compiler_flags["cxxflags"].append("-O2")
            spec.compiler_flags["cxxflags"].append("-fp-speculation=safe")
        super().configure(spec, prefix)

    def setup_build_environment(self, env):
        if "+mpi" in self.spec:
            if self.spec["mpi"].extra_attributes and "ldflags" in self.spec["mpi"].extra_attributes:
                env.append_flags("LDFLAGS", self.spec["mpi"].extra_attributes["ldflags"])

    def get_make_config_options(self, spec, prefix):
        def yes_no(varstr):
            return "YES" if varstr in self.spec else "NO"

        options = super().get_make_config_options(spec, prefix)

        options.append("MFEM_USE_CALIPER=%s" % yes_no("+caliper"))
        if "+caliper" in self.spec: 
            options.append("CALIPER_DIR=%s" % self.spec["caliper"].prefix)
            options.append("MFEM_USE_ADIAK=%s" % yes_no("+adiak"))
            options.append("ADIAK_DIR=%s" % self.spec["adiak"].prefix)

        return options
