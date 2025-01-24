# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack.pkg.builtin.cray_mpich import CrayMpich as BuiltinCM


class CrayMpich(BuiltinCM):

    variant("gtl", default=False, description="enable GPU-aware mode")

    @property
    def libs(self):
        libs = super(CrayMpich, self).libs

        if self.spec.satisfies("+gtl"):
            gtl_lib_prefix = self.spec.extra_attributes["gtl_lib_path"]
            gtl_libs = self.spec.extra_attributes["gtl_libs"]
            libs += find_libraries(gtl_libs, root=gtl_lib_prefix, recursive=True)

        return libs

    def setup_run_environment(self, env):

        super(CrayMpich, self).setup_run_environment(env)

        if self.spec.satisfies("+gtl"):
            env.set("MPICH_GPU_SUPPORT_ENABLED", "1")
            env.prepend_path("LD_LIBRARY_PATH", self.spec.extra_attributes["gtl_lib_path"])
        else:
            env.set("MPICH_GPU_SUPPORT_ENABLED", "0")
            gtl_path = self.spec.extra_attributes.get("gtl_lib_path", "")
            if gtl_path:
                env.prepend_path("LD_LIBRARY_PATH", gtl_path)
