# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling


class Smb(Experiment, StrongScaling):
    variant(
        "workload",
        default="mpi_overhead",
        values=("mpi_overhead", "msgrate", "rma_mt"),
        description="workload",
    )

    variant(
        "version",
        default="master",
        description="app version",
    )

    def compute_applications_section(self):
        if self.spec.satisfies("workload=mpi_overhead"):
            self.add_experiment_variable("n_ranks", "2")
        elif self.spec.satisfies("workload=msgrate") or self.spec.satisfies(
            "workload=rma_mt"
        ):
            self.add_experiment_variable("n_nodes", "1")
            self.add_experiment_variable("n_ranks", "{n_nodes}*{sys_cores_per_node}")

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        spec_string = f"smb@{app_version} +mpi"
        if self.spec.satisfies("workload=rma_mt"):
            spec_string += "+rma"
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        self.add_spack_spec(system_specs["mpi"])
        self.add_spack_spec(self.name, [spec_string, system_specs["compiler"]])
