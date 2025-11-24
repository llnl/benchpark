# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.cray_mpich.package import CrayMpich as BuiltinCM


class CrayMpich(BuiltinCM):

    variant("gtl", default=True, description="enable GPU-aware mode")

    @property
    def libs(self):
        libs = super().libs

        if self.spec.satisfies("+gtl"):
            ld_flags = self.spec.extra_attributes["ldflags"]
            gtl_lib_prefix = self.spec.extra_attributes["gtl_lib_path"]
            # gtl_libs, if set, must be a single string. You can pass multiple
            # libs by adding a space between each
            gtl_libs = self.spec.extra_attributes["gtl_libs"].split()
            libs += find_libraries(gtl_libs, root=gtl_lib_prefix, recursive=True)

        return libs

    def setup_run_environment(self, env):

        super().setup_run_environment(env)

        if self.spec.satisfies("+gtl"):
            env.set("MPICH_GPU_SUPPORT_ENABLED", "1")
            env.prepend_path("LD_LIBRARY_PATH", self.spec.extra_attributes["gtl_lib_path"])
        else:
            env.set("MPICH_GPU_SUPPORT_ENABLED", "0")
            gtl_path = self.spec.extra_attributes.get("gtl_lib_path", "")
            if gtl_path:
                env.prepend_path("LD_LIBRARY_PATH", gtl_path)

    def cmake_args(self):
        args = super().cmake_args(self)

        if self.spec.satisfies("+gtl"):
            # Link GTL for MPICH GPU-aware
            args.append(self.define("CMAKE_EXE_LINKER_FLAGS", self.spec['mpi'].libs.ld_flags))

        return args
