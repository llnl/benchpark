# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack.pkg.builtin.spectrum_mpi import SpectrumMpi as BuiltinSM


class SpectrumMpi(BuiltinSM):
    @property
    def libs(self):
        libnames = [
            'mpi_ibm',
            'mpi_ibm_mpifh',
            'mpiprofilesupport',
            'mpi_ibm_usempi',
        ]
        libs = list('lib' + x for x in libnames)
        return find_libraries(
            libs,
            self.spec.prefix,
            shared=True,
            recursive=True
        )
