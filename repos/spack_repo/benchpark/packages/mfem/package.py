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

    depends_on("camp", when="+umpire")
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

        if "+umpire" in spec:
            umpire = spec["umpire"]
            umpire_opts = umpire.headers
            umpire_libs = umpire.libs
            if "^camp" in umpire:
                umpire_opts += umpire["camp"].headers
                umpire_libs += umpire["camp"].libs
            if "^fmt" in umpire:
                umpire_opts += umpire["fmt"].headers
                umpire_libs += umpire["fmt"].libs
            options = [
                "UMPIRE_OPT=%s" % umpire_opts.cpp_flags if opt.startswith("UMPIRE_OPT=")
                else "UMPIRE_LIB=%s" % self.ld_flags_from_library_list(umpire_libs) if opt.startswith("UMPIRE_LIB=")
                else opt for opt in options
            ]

        options.append("MFEM_USE_CALIPER=%s" % yes_no("+caliper"))
        if "+caliper" in self.spec: 
            options.append("CALIPER_DIR=%s" % self.spec["caliper"].prefix)
            options.append("MFEM_USE_ADIAK=%s" % yes_no("+adiak"))
            options.append("ADIAK_DIR=%s" % self.spec["adiak"].prefix)

        return options

    @run_after("install")
    def install_cmake_config(self):
        """Generate and install a CMake config file for packages that want to use find_package(mfem)"""
        cmake_dir = join_path(self.prefix.lib, "cmake", "mfem")
        mkdirp(cmake_dir)

        # mfem is a static library whose object code references symbols from
        # RAJA, hipsparse, hipblas, and other deps. CMake consumers must link
        # these transitively, but the generated cmake config doesn't record
        # them. mfem itself writes the authoritative list to config.mk as
        # MFEM_EXT_LIBS; parse that rather than guessing from the spack graph.
        interface_link_flags = []
        config_mk = join_path(self.prefix, "share", "mfem", "config.mk")
        if os.path.exists(config_mk):
            with open(config_mk) as f:
                for line in f:
                    if line.startswith("MFEM_EXT_LIBS"):
                        _, _, value = line.partition("=")
                        interface_link_flags = value.strip().split()
                        break

        interface_libs_property = ""
        if interface_link_flags:
            # CMake expects a semicolon-separated list for INTERFACE_LINK_LIBRARIES.
            # The flags from MFEM_EXT_LIBS are space-separated shell tokens; join them.
            libs_list = ";".join(interface_link_flags)
            interface_libs_property = (
                '\n        INTERFACE_LINK_LIBRARIES "' + libs_list + '"'
            )

        config_content = """# Determine the installation prefix relative to this file:
#   <prefix>/lib/cmake/mfem/MFEMConfig.cmake
get_filename_component(_MFEM_PREFIX
    "${CMAKE_CURRENT_LIST_DIR}/../../.."
    ABSOLUTE
)

set(MFEM_INCLUDE_DIR "${_MFEM_PREFIX}/include")
set(MFEM_INCLUDE_DIRS "${MFEM_INCLUDE_DIR}")

find_library(MFEM_LIBRARY
    NAMES mfem
    PATHS
        "${_MFEM_PREFIX}/lib"
        "${_MFEM_PREFIX}/lib64"
    NO_DEFAULT_PATH
    REQUIRED
)

set(MFEM_LIBRARIES mfem)

if(NOT TARGET mfem)
    add_library(mfem UNKNOWN IMPORTED)

    set_target_properties(mfem PROPERTIES
        IMPORTED_LOCATION "${MFEM_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${MFEM_INCLUDE_DIR}"\
""" + interface_libs_property + """
    )
endif()

set(MFEM_FOUND TRUE)

unset(_MFEM_PREFIX)
"""

        config_file = join_path(cmake_dir, "MFEMConfig.cmake")
        with open(config_file, "w") as f:
            f.write(config_content)
