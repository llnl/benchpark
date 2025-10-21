# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import warnings

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
            "rocm",
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

        def compute_package_section(self):
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
                elif self.spec.satisfies("caliper=rocm"):
                    rocm_support = (
                        self.spec.satisfies("caliper=rocm") and True
                    )  # check if target system supports rocm
                    if rocm_support:
                        package_specs["caliper"][
                            "pkg_spec"
                        ] += "~papi+rocm amdgpu_target={}".format(
                            system_specs["rocm_arch"]
                        )
                    else:
                        raise NotImplementedError(
                            "Target system does not support the rocm interface"
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

        def compute_variables_section(self):
            """Add Caliper metadata variables for the ramble.yaml"""
            if not self.spec.satisfies("caliper=none"):
                metadata_dict = {
                    "application_name": "{application_name}",
                    "experiment_name": "{experiment_name}",
                    "n_nodes": "{n_nodes}",
                    "n_ranks": "{n_ranks}",
                    "n_threads_per_proc": "{n_threads_per_proc}",
                    "n_resources": "{n_resources}",
                    "process_problem_size": "{process_problem_size}",
                    "total_problem_size": "{total_problem_size}",
                }
                # parse the spec for more metadata
                for i, variant_spec in enumerate(str.split(str(self.spec.variants))):
                    values = variant_spec.split("=")
                    if len(values) == 1:
                        if i == 0:
                            metadata_dict["benchpark_spec"] = values
                        elif values[0] == "'":
                            pass
                    elif len(values) == 2:
                        metadata_dict[values[0]] = values[1]
                    else:
                        warnings.warn(
                            "Possible incorrect values sent to Caliper as metadata"
                        )
                return {"caliper_metadata": metadata_dict}
            else:
                return {}
