# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper


class Hwloc:
    variant(
        "hwloc",
        default="none",
        values=("none", "on"),
        multi=False,
        description="Get underlying infrastructure topology",
    )

    class Helper(ExperimentHelper):
        def compute_modifiers_section(self):
            modifier_list = []

            if not self.spec.satisfies("hwloc=none"):
                affinity_modifier_modes = {}
                affinity_modifier_modes["name"] = "hwloc"
                affinity_modifier_modes["mode"] = self.spec.variants["hwloc"][0]
                modifier_list.append(affinity_modifier_modes)

            return modifier_list
