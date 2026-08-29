# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.build_systems.cached_cmake import (
    cmake_cache_option,
    cmake_cache_string,
)
from spack_repo.builtin.packages.camp.package import Camp as BuiltinCamp


class Camp(BuiltinCamp):

    version(
        "2026.07.1",
        tag="v2026.07.1",
        commit="390c5e05159a5a88545a7c5c9f1fdbbb3f64f120",
        submodules=False,
    )
