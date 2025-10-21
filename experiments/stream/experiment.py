# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment


class Stream(
    Experiment,
    MpiOnlyExperiment,
    Caliper,
):
    variant(
        "workload",
        default="stream",
        description="stream",
    )

    variant(
        "version",
        default="5.10-caliper",
        values=("develop", "latest", "5.10-caliper"),
        description="app version",
    )

    maintainers("daboehme", "rfhaque")

    def compute_applications_section(self):

        array_size = {"s": 650000000}

        self.add_experiment_variable("processes_per_node", "1", named=True)
        self.add_experiment_variable("n", "35", False)
        self.add_experiment_variable("o", "0", False)
        self.add_experiment_variable("n_ranks", 1, True)
        self.add_experiment_variable(
            "n_threads_per_proc", [16, 32], named=True, matrixed=True
        )

        for pk, pv in array_size.items():
            self.add_experiment_variable(pk, pv, True)

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{n}/{n_ranks}",
            total_problem_size="{n}",
        )

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"stream{self.determine_version()}"])
