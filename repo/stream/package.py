# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class Stream(CMakePackage):
    """The STREAM benchmark is a simple synthetic benchmark program that
    measures sustainable memory bandwidth (in MB/s) and the corresponding
    computation rate for simple vector kernels.

    This package builds a fork of the official code with Caliper support, 
    a CMake build system, and the ability to configure settings 
    (array size, iterations, offset) at runtime via the command line."""

    homepage = "https://www.cs.virginia.edu/stream/ref.html"
    git = "https://github.com/daboehme/STREAM.git"

    version("5.10-caliper", git="https://github.com/daboehme/STREAM.git",
            branch="caliper-benchpark")

    variant("caliper", default=False, description="Enable Caliper/Adiak support")

    requires("@5.10-caliper", when="+caliper")

    depends_on("c", type="build")
    depends_on("fortran", type="build")

    depends_on("caliper", when="+caliper")
    depends_on("adiak@0.4:", when="+caliper")

    def cmake_args(self):
        args = [ 
            self.define_from_variant("STREAM_ENABLE_CALIPER", "caliper") 
        ]

        return args
