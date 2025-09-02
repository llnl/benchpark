# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment


class SalmonTddft(Experiment, MpiOnlyExperiment, OpenMPExperiment):
    variant(
        "workload",
        default="gs",
        values=("gs", "rt"),
        multi=True,
        description="salmon-tddft",
    )

    variant(
        "version",
        default="2.0.0",
        description="app version",
    )

    def compute_applications_section(self):
        self.add_experiment_variable("experiment_setup", "")

        if self.spec.satisfies("workload=gs"):
            self.add_experiment_variable("exercise", "exercise_01_C2H2_gs")
            self.add_experiment_variable("inp_file", "C2H2_gs.inp")
        elif self.spec.satisfies("workload=rt"):
            self.add_experiment_variable("exercise", "exercise_03_C2H2_rt")
            self.add_experiment_variable("inp_file", "C2H2_rt_pulse.inp")
            self.add_experiment_variable(
                "restart_data",
                "../../gs/salmon_{n_nodes}_{n_ranks}_{n_threads}/data_for_restart/",
            )

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("omp_num_threads", ["12"])
        self.add_experiment_variable("n_ranks", "{processes_per_node} * {n_nodes}")
        self.add_experiment_variable("processes_per_node", ["4"])
        self.add_experiment_variable("n_nodes", ["1"], True)

        self.set_required_variables(
            n_resources="{n_ranks}", process_problem_size="", total_problem_size=""
        )

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"salmon-tddft{self.determine_version()}"])
