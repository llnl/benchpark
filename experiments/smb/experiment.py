# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment


class Smb(Experiment, MpiOnlyExperiment):
    variant(
        "workload",
        default="mpi_overhead",
        values=("mpi_overhead", "msgrate", "rma_mt"),
        description="workload",
    )

    variant(
        "version",
        default="1.1",
        values=("master", "latest", "1.1"),
        description="app version",
    )

    maintainers("nhanford")

    def compute_applications_section(self):
        if self.spec.satisfies("workload=mpi_overhead"):
            self.add_experiment_variable("n_ranks", "2")
        elif self.spec.satisfies("workload=msgrate") or self.spec.satisfies(
            "workload=rma_mt"
        ):
            self.add_experiment_variable("n_nodes", "1")
            self.add_experiment_variable("n_ranks", "{n_nodes}*{sys_cores_per_node}")

        self.set_required_variables(
            n_resources="{n_ranks}", process_problem_size="", total_problem_size=""
        )

    def compute_package_section(self):
        spec_string = f"smb{self.determine_version()}"
        if self.spec.satisfies("workload=rma_mt"):
            spec_string += "+rma"
        self.add_package_spec(self.name, [spec_string])
