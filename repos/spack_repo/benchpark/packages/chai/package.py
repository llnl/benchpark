# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.build_systems.cached_cmake import (
    cmake_cache_option,
    cmake_cache_string,
)
from spack_repo.builtin.packages.chai.package import Chai as BuiltinChai


class Chai(BuiltinChai):
    variant(
        "cxxstd",
        default="17",
        values=("11", "14", "17", "20"),
        description="C++ standard to build with",
    )

    @property
    def cxx_std(self):
        return self.spec.variants.get("cxxstd").value

    def initconfig_package_entries(self):
        spec = self.spec
        entries = super().initconfig_package_entries()

        # C++ standard
        entries.append(cmake_cache_string("BLT_CXX_STD", f"c++{self.cxx_std}"))

        return entries
