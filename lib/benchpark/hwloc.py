# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from enum import Enum

from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper


class HwlocVariantValues(str, Enum):
    NONE = "none"
    ON = "on"


class Hwloc:
    variant(
        "hwloc",
        default=HwlocVariantValues.NONE.value,
        values=tuple(v.value for v in HwlocVariantValues),
        multi=False,
        description="Get underlying infrastructure topology",
    )

    class Helper(ExperimentHelper):
        def compute_modifiers_section(self):
            modifier_list = []

            if not self.spec.satisfies(f"hwloc={HwlocVariantValues.NONE.value}"):
                affinity_modifier_modes = {}
                affinity_modifier_modes["name"] = "hwloc"
                affinity_modifier_modes["mode"] = self.spec.variants["hwloc"][0]
                modifier_list.append(affinity_modifier_modes)

            return modifier_list
