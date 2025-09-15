# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

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

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    depends_on("mpi@1.1:")
    depends_on("caliper", when="+caliper") 
    depends_on("adiak", when="+caliper") 

    def cmake_args(self):
        build_targets = ["all", "docs"]
        install_targets = ["install", "docs"]
        args = [
            "-DHPCG_ENABLE_MPI=TRUE",
            self.define_from_variant("HPCG_ENABLE_CALIPER", "caliper"),
            self.define_from_variant("HPCG_ENABLE_OPENMP", "openmp"),
        ]
        
        return args
