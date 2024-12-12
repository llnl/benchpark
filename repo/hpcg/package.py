# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
import platform

from spack.package import *


class Hpcg(CMakePackage):
    """HPCG is a software package that performs a fixed number of multigrid
    preconditioned (using a symmetric Gauss-Seidel smoother) conjugate gradient
    (PCG) iterations using double precision (64 bit) floating point values."""

    #homepage = "https://www.hpcg-benchmark.org"
    #url = "https://www.hpcg-benchmark.org/downloads/hpcg-3.1.tar.gz"
    git = "https://github.com/daboehme/hpcg.git"

    version("develop", branch="master")
    #version("3.1", sha256="33a434e716b79e59e745f77ff72639c32623e7f928eeb7977655ffcaade0f4a4")
    version("caliper", branch="caliper-support")
    
    variant("openmp", default=True, description="Enable OpenMP support")
    variant("caliper", default=False, description="Enable Caliper support")
    
    depends_on("mpi@1.1:")
    depends_on("caliper", when="+caliper") 
    depends_on("adiak", when="+caliper") 

    """
    patch(
        "https://github.com/daboehme/hpcg/commit/114602d458d1034faa52b71e4c15aba9b3a17698.patch?full_index=1",
        #sha256="b13c74454a2166767e3cde77b0f1d080522828122defc8477cc0b9919dcc231a",
        sha256="1200e257da66c1824cc19f37f5df12d8b34ad7f738dd978d119ade0ac14da802",
        when="%gcc@9:",
    )   
    patch(
        "https://github.com/daboehme/hpcg/commit/114602d458d1034faa52b71e4c15aba9b3a17698.patch?full_index=1",
        #sha256="b13c74454a2166767e3cde77b0f1d080522828122defc8477cc0b9919dcc231a",
        sha256="1200e257da66c1824cc19f37f5df12d8b34ad7f738dd978d119ade0ac14da802",
        when="%aocc",
    )   
    patch(
        "https://github.com/daboehme/hpcg/commit/114602d458d1034faa52b71e4c15aba9b3a17698.patch?full_index=1",
        #sha256="b13c74454a2166767e3cde77b0f1d080522828122defc8477cc0b9919dcc231a",
        sha256="1200e257da66c1824cc19f37f5df12d8b34ad7f738dd978d119ade0ac14da802",
        when="%arm",
    )   
    patch(
        "https://github.com/daboehme/hpcg/commit/114602d458d1034faa52b71e4c15aba9b3a17698.patch?full_index=1",
        #sha256="b13c74454a2166767e3cde77b0f1d080522828122defc8477cc0b9919dcc231a",
        sha256="1200e257da66c1824cc19f37f5df12d8b34ad7f738dd978d119ade0ac14da802",
        when="%oneapi",
    )
    patch(
        "https://github.com/daboehme/hpcg/commit/114602d458d1034faa52b71e4c15aba9b3a17698.patch?full_index=1",
        #sha256="b13c74454a2166767e3cde77b0f1d080522828122defc8477cc0b9919dcc231a",
        sha256="1200e257da66c1824cc19f37f5df12d8b34ad7f738dd978d119ade0ac14da802",
        when="%intel",
    )
    patch(
        "https://github.com/daboehme/hpcg/commit/114602d458d1034faa52b71e4c15aba9b3a17698.patch?full_index=1",
        #sha256="b13c74454a2166767e3cde77b0f1d080522828122defc8477cc0b9919dcc231a",
        sha256="1200e257da66c1824cc19f37f5df12d8b34ad7f738dd978d119ade0ac14da802",
        when="%clang",
    )
    """

    def cmake_args(self):
        build_targets = ["all", "docs"]
        install_targets = ["install", "docs"]
        args = [
            "-DHPCG_ENABLE_MPI=TRUE",
            self.define_from_variant("-DHPCG_ENABLE_CALIPER=TRUE", "caliper"),
            self.define_from_variant("-DHPCG_ENABLE_OPENMP=TRUE", "openmp"),
        ]
        return args
