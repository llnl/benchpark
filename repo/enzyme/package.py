# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class Enzyme(CMakePackage):
    """Enzyme"""

    git = "https://github.com/jandrej/Enzyme.git"

    tags = ["enzyme"]

    license("Apache-2.0")

    maintainers("jandrej")

    version("patch-1", branch="patch-1")

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    depends_on("llvm@18:")

    root_cmakelists_dir = "enzyme"

    def cmake_args(self):
        cmake_options = [
            f"-DLLVM_DIR={self.spec['llvm'].prefix}",
        ]

        return cmake_options
