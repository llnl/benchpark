# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
from spack.package import *
from spack_repo.builtin.packages.cray_mpich.package import CrayMpich as BuiltinCM

class CrayMpich(BuiltinCM):
    """Cray MPICH with optional GPU-aware GTL support."""
    variant("gtl", default=True, description="enable GPU-aware mode")

    @property
    def libs(self):
        # if +gtl is off just return the base libs
        if "+gtl" not in self.spec:
            return super().libs

        # support both old ("gtl_lib_path") and new ("gtl_path") semantics
        gtl_prefix = (
            self.spec.extra_attributes.get("gtl_lib_path")
            or self.spec.extra_attributes.get("gtl_path")
        )
        if not gtl_prefix:
            raise InstallError(
                "variant +gtl requires extra_attributes['gtl_lib_path'] or ['gtl_path']"
            )

        # if the user pointed at the top-level install, append /lib
        if os.path.basename(gtl_prefix) != "lib":
            gtl_prefix = os.path.join(gtl_prefix, "lib")

        base_libs = super().libs
        gtl_libs = self.spec.extra_attributes["gtl_libs"].split()
        base_libs += find_libraries(gtl_libs, root=gtl_prefix, recursive=True)
        return base_libs

    def setup_run_environment(self, env):
        super().setup_run_environment(env)

        # turn GPU support on/off
        enabled = "1" if "+gtl" in self.spec else "0"
        env.set("MPICH_GPU_SUPPORT_ENABLED", enabled)

        if "+gtl" in self.spec:
            # if the old key is set, use it
            if "gtl_lib_path" in self.spec.extra_attributes:
                env.prepend_path("LD_LIBRARY_PATH",
                                 self.spec.extra_attributes["gtl_lib_path"])
            else:
                # otherwise assume gtl_path points at the install root, add /lib
                gtl_top = self.spec.extra_attributes.get("gtl_path", "")
                if gtl_top:
                    env.prepend_path("LD_LIBRARY_PATH", os.path.join(gtl_top, "lib"))

    def cmake_args(self):
        args = super().cmake_args()
        if "+gtl" in self.spec:
            args.append(
                self.define("CMAKE_EXE_LINKER_FLAGS",
                            self.spec["mpi"].libs.ld_flags)
            )
        return args
