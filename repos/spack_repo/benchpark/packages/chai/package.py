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
    variant("single_memory", default=False, description="Enable single memory space model")

    variant(
        "cxxstd",
        default="17",
        values=("11", "14", "17", "20"),
        description="C++ standard to build with",
    )

    conflicts("+single_memory", when="~rocm")

    version(
        "2025.12.0",
        tag="v2025.12.0",
        commit="26d5646707e1848b0524379b12a7716e4a830a27",
        submodules=False,
    )

    @property
    def cxx_std(self):
        return self.spec.variants.get("cxxstd").value

    def initconfig_hardware_entries(self):
        spec = self.spec
        entries = super().initconfig_hardware_entries()

        if spec.satisfies("+single_memory"):
            entries.append(cmake_cache_option("CHAI_THIN_GPU_ALLOCATE", True))
            entries.append(cmake_cache_option("CHAI_DISABLE_RM", True))

        return entries

    def initconfig_package_entries(self):
        spec = self.spec
        entries = super().initconfig_package_entries()

        # C++ standard
        entries.append(cmake_cache_string("BLT_CXX_STD", f"c++{self.cxx_std}"))

        return entries