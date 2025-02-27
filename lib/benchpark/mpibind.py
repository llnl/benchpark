# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper

'''
class Mpibind:
    variant(
        "mpibind",
        default="standard",
        values=(
            "standard",
            "on",
            "off",
            "v",
            "vv",
            "greedy:0",
        ),
        multi=False,
        description="Toggle mpibind and set verbosity",
    )

    class Helper(ExperimentHelper):
        def compute_modifiers_section(self):
            modifier_list = [{"name": "mpibind"}]
            if not self.spec.satisfies("mpibind=off"):
                mpibind_modifier_modes = {}
                mpibind_modifier_modes["name"] = "allocation"
                mpibind_modifier_modes["mode"] = self.spec.variants["mpibind"][0]
                #modifier_list.set()
                #print(mpibind_modifier_modes)
                modifier_list[0]["mode"] = mpibind_modifier_modes["mode"]
            return modifier_list
'''
