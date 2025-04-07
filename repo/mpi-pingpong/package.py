# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class MpiPingpong(CMakePackage):

    git = "https://github.com/stephanielam3211/benchmark.git"

    variant("caliper", default=False, description="Enable Caliper/Adiak support")

    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")    

    def cmake_args(self):
        args = [
            "-DUSE_CALIPER"
        ]
        return args