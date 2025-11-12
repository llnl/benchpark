# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
import os.path

class CrayMpichWrappers(BundlePackage):

    version("1.0.0")

    def install(self, spec, prefix):
        with open(os.path.join(prefix, "FindMPI.cmake"), "w") as f:
            f.write("""\
include_guard(GLOBAL)

include("${CMAKE_ROOT}/Modules/FindMPI.cmake")

message("cray-mpich-wrappers test231 module")

if(TARGET MPI::MPI_C)
  if(NOT DEFINED MPI_C_EXTRA_FLAGS)
    set(MPI_C_EXTRA_FLAGS "-ltest231")
  endif()
  if(MPI_C_EXTRA_FLAGS)
    separate_arguments(MPI_C_EXTRA_FLAGS NATIVE_COMMAND)
    target_compile_options(MPI::MPI_C INTERFACE ${MPI_C_EXTRA_FLAGS})
  endif()
endif()
""")
