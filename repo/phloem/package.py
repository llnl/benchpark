# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
# 
# SPDX-License-Identifier: Apache-2.0

from spack.package import *

class Phloem(MakefilePackage):
    tags = []

    url = "https://github.com/LLNL/phloem/archive/refs/tags/v1.4.5.tar.gz"
    git = "https://github.com/LLNL/phloem"

    maintainers("knox10")

    version("master", branch="master")

    variant("mpi", default=False, description="Build with MPI support")
    
    depends_on("mpi", when="+mpi")

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        mkdir(prefix.doc)
        install("mpigraph-1.6/mpiBench/mpiBench", prefix.bin)
        install("sqmr-1.1.0/sqmr", prefix.bin)
        install("mpigraph-1.6/mpiGraph/mpiGraph", prefix.bin)
        install("presta-1.3.0/com", prefix.bin)
        install("presta-1.3.0/bw.message.sizes", prefix.bin)
        install("presta-1.3.0/latency.message.sizes", prefix.bin)
        install("README", prefix.doc)
