# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper


class Hwloc:
    variant(
        "hwloc",
        default="on",
        values=(
            "on",
            "off"
        ),
        multi=False,
        description="Get infrastructure underlying topology",
    )

    class Helper(ExperimentHelper):
        def compute_modifiers_section(self):
            return [{"name": "hwloc"}]