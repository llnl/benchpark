# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling


class Gpcnet(Experiment, StrongScaling):
    variant(
        "workload",
        default="network_test",
        values=("network_test", "network_load_test"),
        description="network_test or network_load_test",
    )

    variant(
        "version",
        default="master",
        description="app version",
    )

    def compute_applications_section(self):
        # TODO: Replace with conflicts clause
        self.add_experiment_variable(
            "n_ranks", "{n_nodes}*{sys_cores_per_node}//2", True
        )
        if self.spec.satisfies("workload=network_test"):
            self.add_experiment_variable("n_nodes", ["2", "4"])
        elif self.spec.satisfies("workload=network_load_test"):
            self.add_experiment_variable("n_nodes", "10")

    def compute_package_section(self, pkg_manager):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"

        # empty package_specs value implies external package
        self.add_package_spec(system_specs["mpi"])

        self.add_package_spec(
            self.name, [f"gpcnet@{app_version} +mpi", system_specs["compiler"]]
        )
