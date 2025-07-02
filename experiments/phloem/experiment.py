# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling


class Phloem(Experiment, StrongScaling):
    variant(
        "workload",
        default="sqmr",
        values=("sqmr", "mpiBench", "mpiGraph"),
        description="sqmr, mpiBench, or mpiGraph",
    )

    variant(
        "version",
        default="master",
        description="app version",
    )

    maintainers("nhanford")

    def compute_applications_section(self):
        if self.spec.satisfies("workload=sqmr"):
            self.add_experiment_variable(
                "n_ranks", "{num_cores}*{num_nbors}+{num_cores}"
            )
            self.add_experiment_variable("num_cores", "4")
            self.add_experiment_variable("num_nbors", "{num_cores}")
        elif self.spec.satisfies("workload=mpiBench"):
            self.add_experiment_variable("n_ranks", "2")
        elif self.spec.satisfies("workload=mpiGraph"):
            self.add_experiment_variable("n_ranks", "2")

        self.set_required_variables(
            n_resources="{n_ranks}", process_problem_size="", total_problem_size=""
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"phloem@{app_version} +mpi"])
