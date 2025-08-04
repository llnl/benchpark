# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class MpiPingpong(CMakePackage):

    git = "https://github.com/LLNL/microbenchmarks.git"

    version("develop", branch="develop")

    variant("caliper", default=False, description="Enable Caliper/Adiak support")

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
        return args

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        install(join_path(self.build_directory, "pingpong"), prefix.bin)
