# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper


class Affinity:
    variant(
        "affinity",
        default="none",
        values=(
            "none",
            "mpi",
            "cuda",
            "rocm",
        ),
        multi=False,
        description="Build and run the affinity package",
    )

    class Helper(ExperimentHelper):
        def compute_modifiers_section(self):
            modifier_list = []
            if not self.spec.satisfies("affinity=none"):
                affinity_modifier_modes = {}
                affinity_modifier_modes["name"] = "affinity"
                affinity_modifier_modes["mode"] = self.spec.variants["affinity"][0]
                modifier_list.append(affinity_modifier_modes)
            return modifier_list

        def compute_spack_section(self):
            # set package versions
            affinity_version = "master"

            # get system config options
            # TODO: Get compiler/mpi/package handles directly from system.py
            system_specs = {}
            system_specs["compiler"] = "default-compiler"
            if self.spec.satisfies("affinity=cuda"):
                system_specs["cuda_arch"] = "{cuda_arch}"
            if self.spec.satisfies("affinity=rocm"):
                system_specs["rocm_arch"] = "{rocm_arch}"

            # set package spack specs
            package_specs = {}

            if not self.spec.satisfies("affinity=none"):
                package_specs["affinity"] = {
                    "pkg_spec": f"affinity@{affinity_version}+mpi",
                    "compiler": system_specs["compiler"],
                }
                if self.spec.satisfies("affinity=cuda"):
                    package_specs["affinity"]["pkg_spec"] += "+cuda"
                elif self.spec.satisfies("affinity=rocm"):
                    package_specs["affinity"]["pkg_spec"] += "+rocm"

            return {
                "packages": {k: v for k, v in package_specs.items() if v},
                "environments": {"affinity": {"packages": list(package_specs.keys())}},
            }
