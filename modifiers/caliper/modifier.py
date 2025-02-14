# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.modkit import *


class Caliper(BasicModifier):
    """Define a modifier for Caliper"""

    name = "caliper"

    tags("profiler", "performance-analysis")

    maintainers("pearce8")

    mode(
        name="default",
        description="Enable caliper tracking",
    )

    software_spec("caliper", pkg_spec="caliper")

    required_package("caliper")
