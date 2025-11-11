# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class Ad(CMakePackage):
    """AD Benchmark"""

    git = "git@github.com:jandrej/dfem-enzyme-compat.git"

    tags = ["benchmark"]

    license("Apache-2.0")

    maintainers("jandrej")

    version("main", branch="main")

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    depends_on("enzyme")

    def cmake_args(self):
        cmake_options = [
            f"-DENZYME_DIR={self.spec['enzyme'].prefix}",
        ]

        return cmake_options

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        install(join_path(self.build_directory, "src", "c_interface_test"), prefix.bin)
