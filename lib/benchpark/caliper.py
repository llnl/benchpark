# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper


class Caliper:
    variant(
        "caliper",
        default="none",
        values=(
            "none",
            "time",
            "mpi",
            "cuda",
            "topdown-counters-all",
            "topdown-counters-toplevel",
            "topdown-all",
            "topdown-toplevel",
        ),
        multi=True,
        description="caliper mode",
    )

    class Helper(ExperimentHelper):
        def compute_modifiers_section(self):
            modifier_list = []
            if not self.spec.satisfies("caliper=none"):
                for var in list(self.spec.variants["caliper"]):
                    if var != "time":
                        caliper_modifier_modes = {}
                        caliper_modifier_modes["name"] = "caliper"
                        caliper_modifier_modes["mode"] = var
                        modifier_list.append(caliper_modifier_modes)
                # Add time as the last mode
                modifier_list.append({"name": "caliper", "mode": "time"})
            return modifier_list

        def compute_spack_section(self):
            # set package versions
            caliper_version = "master"

            # get system config options
            # TODO: Get compiler/mpi/package handles directly from system.py
            system_specs = {}
            system_specs["compiler"] = "default-compiler"
            if self.spec.satisfies("caliper=cuda"):
                system_specs["cuda_arch"] = "{cuda_arch}"
            if self.spec.satisfies("caliper=rocm"):
                system_specs["rocm_arch"] = "{rocm_arch}"

            # set package spack specs
            package_specs = {}

            if not self.spec.satisfies("caliper=none"):
                package_specs["caliper"] = {
                    "pkg_spec": f"caliper@{caliper_version}+adiak+mpi~libunwind~libdw",
                    "compiler": system_specs["compiler"],
                }
                if any("topdown" in var for var in self.spec.variants["caliper"]):
                    papi_support = True  # check if target system supports papi
                    if papi_support:
                        package_specs["caliper"]["pkg_spec"] += "+papi"
                    else:
                        raise NotImplementedError(
                            "Target system does not support the papi interface"
                        )
                elif self.spec.satisfies("caliper=cuda"):
                    cuda_support = (
                        self.spec.satisfies("caliper=cuda") and True
                    )  # check if target system supports cuda
                    if cuda_support:
                        package_specs["caliper"][
                            "pkg_spec"
                        ] += "~papi+cuda cuda_arch={}".format(system_specs["cuda_arch"])
                    else:
                        raise NotImplementedError(
                            "Target system does not support the cuda interface"
                        )
                elif self.spec.satisfies("caliper=time") or self.spec.satisfies(
                    "caliper=mpi"
                ):
                    package_specs["caliper"]["pkg_spec"] += "~papi"

            return {
                "packages": {k: v for k, v in package_specs.items() if v},
                "environments": {"caliper": {"packages": list(package_specs.keys())}},
            }

        def get_helper_name_prefix(self):
            if not self.spec.satisfies("caliper=none"):
                caliper_prefix = ["caliper"]
                for var in list(self.spec.variants["caliper"]):
                    if self.spec.satisfies(f"caliper={var}"):
                        caliper_prefix.append(var.replace("-", "_"))
                return "_".join(caliper_prefix)
            else:
                return "caliper_none"

        def get_spack_variants(self):
            return "~caliper" if self.spec.satisfies("caliper=none") else "+caliper"
