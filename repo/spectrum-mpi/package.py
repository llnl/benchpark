# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import spack.pkg.builtin.spectrum_mpi

class SpectrumMpi(spack.pkg.builtin.spectrum_mpi.SpectrumMpi):
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
