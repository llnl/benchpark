# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class MpiPingpong(CMakePackage):

    git = "https://github.com/LLNL/microbenchmarks.git"

    version("addHip", branch="addHip")

    variant("caliper", default=False, description="Enable Caliper/Adiak support")
    variant("openmp", default=True, description="Enable OpenMP support")

    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")

    root_cmakelists_dir = "repo/pingpong"

    def cmake_args(self):
        if self.spec.satisfies("+caliper"):
            args = [
                "-DUSE_CALIPER=ON"
            ]
        else:
            args = [
                "-DUSE_CALIPER=OFF"
            ]

        if '+openmp' in spec:
            args.append('-DUSE_OPENMP=ON')

        return args
        
    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        install(join_path(self.build_directory, "pingpong"), prefix.bin)
