# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.umpire.package import Umpire as BuiltinUmpire


class Umpire(BuiltinUmpire):

    version(
        "2026.07.1",
        tag="v2026.07.1",
        commit="5639f6c1fd4ca1fed7f0f1f48dcbbfbd00899484",
        submodules=False,
    )

    version(
        "2025.12.0",
        tag="v2025.12.0",
        commit="0372fbd6e1f17d7e6dd72693f8b857f3ec7559e9",
        submodules=False,
    )
    
    depends_on("fmt@9.1: cxxstd=17", when="@2024.02.0: %oneapi")
