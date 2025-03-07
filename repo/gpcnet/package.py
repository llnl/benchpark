# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *

class Gpcnet(MakefilePackage):


    tags = ["proxy-app"]

    homepage = "https://codesign.llnl.gov/quicksilver.php"
    url = "https://github.com/netbench/GPCNET/archive/refs/tags/1.2.tar.gz"
    git = "https://github.com/netbench/GPCNET"

    maintainers("knox10")

    version("master", branch="master")

    variant("mpi", default=False, description="Build with MPI support")
    
    depends_on("mpi", when="+mpi")

    @property
    def build_targets(self):
        targets = ["all"]
        return targets

    def edit(self, spec, prefix):
        makefile = FileFilter("Makefile")
        makefile.filter('CC = cc', "CC = {0}".format(spec["mpi"].mpicc))


    def install(self, spec, prefix):
        mkdir(prefix.bin)
        mkdir(prefix.doc)
        install("network_test", prefix.bin)
        install("network_load_test", prefix.bin)
        install("LICENSE", prefix.doc)
        install("README.md", prefix.doc)
