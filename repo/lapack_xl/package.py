# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class LapackXl(Package):

    provides("lapack")

    @property
    def lapack_libs(self):
        libname = ["liblapack", "libblas"]
        return find_libraries(libname, root=self.prefix.lib, shared=False, recursive=False)

    @property
    def libs(self):
        libname = ["liblapack", "libblas"]
        return find_libraries(libname, root=self.prefix.lib, shared=False, recursive=False)
