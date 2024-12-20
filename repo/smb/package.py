# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0
from spack.package import *
import llnl.util.filesystem as fs
import inspect
class Smb(MakefilePackage):
    tags = []

    url = "https://github.com/sandialabs/SMB/archive/refs/tags/1.1.tar.gz"
    git = "https://github.com/sandialabs/SMB"

    maintainers("knox10")

    version("master", branch="master")

    variant("mpi", default=False, description="Build with MPI support")
    variant("rma", default=False, description="Build RMA-MT variant")    
    depends_on("mpi", when="+mpi")
    build_directory = ["src/mpi_overhead"]
    
    def edit(self, spec, prefix):
        if "+rma" in spec:
            makefile = FileFilter("src/rma_mt_mpi/Makefile")
            makefile.filter('CC=cc', "CC = {0}".format(spec["mpi"].mpicc))
    #TODO: add shm variant
    def build(self, spec, prefix):
        if "+rma" in spec: 
            self.build_directory.append("src/rma_mt_mpi")
        else:
            self.build_directory.append("src/msgrate")

        for path in self.build_directory:
            with fs.working_dir(path):
                make()
    def install(self, spec, prefix):
        mkdir(prefix.bin)
        mkdir(prefix.doc)
        install("src/mpi_overhead/mpi_overhead", prefix.bin)
        install("src/mpi_overhead/README", prefix.doc)
        if "+rma" in spec:
            install("src/rma_mt_mpi/msgrate", prefix.bin)
        else:
            install("src/msgrate/msgrate", prefix.bin)
            install("src/msgrate/README", prefix.doc)
