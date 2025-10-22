# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment


class Gpcnet(Experiment, MpiOnlyExperiment):
    variant(
        "workload",
        default="network_test",
        values=("network_test", "network_load_test"),
        description="network_test or network_load_test",
    )

    variant(
        "version",
        default="master",
        values=("master", "latest"),
        description="app version",
    )

    maintainers("rfhaque")

    def compute_applications_section(self):
        # TODO: Replace with conflicts clause
        self.add_experiment_variable(
            "n_ranks", "{n_nodes}*{sys_cores_per_node}//2", True
        )
        if self.spec.satisfies("workload=network_test"):
            self.add_experiment_variable("n_nodes", ["2", "4"])
        elif self.spec.satisfies("workload=network_load_test"):
            self.add_experiment_variable("n_nodes", "10")

        self.set_required_variables(
            n_resources="{n_ranks}", process_problem_size="", total_problem_size=""
        )

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"gpcnet{self.determine_version()}"])
