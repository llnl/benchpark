# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack.pkg.builtin.essl import Essl as BuiltinEssl


class Essl(BuiltinEssl):
    @property
    def lapack_libs(self):
        essl_libs = super(Essl, self).lapack_libs

        essl_libs += find_libraries(
            ["libessl", "libessl6464", "libesslsmp", "libesslsmp6464"], root=self.prefix.lib64, shared=True
        )
        return essl_libs
