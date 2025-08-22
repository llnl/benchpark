# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.scaling import ScalingMode, Scaling
from benchpark.caliper import Caliper


class Hpl(
    Experiment,
    MpiOnlyExperiment,
    OpenMPExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak),
    Caliper,
):

    variant(
        "workload",
        default="standard",
        description="workload to use",
    )

    variant(
        "version",
        default="2.3-caliper",
        values=("latest", "2.3-caliper", "2.3", "2.2"),
        description="app version",
    )

    maintainers("daboehme")

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            self.add_experiment_variable("n_nodes", 1, True)
            self.add_experiment_variable("Ns", 10000, True)

            self.add_experiment_variable("N-Grids", 1, False)
            self.add_experiment_variable("Ps", "4 * {n_nodes}", True)
            self.add_experiment_variable("Qs", "8", False)

            self.add_experiment_variable("N-Ns", 1, False)

            self.add_experiment_variable("N-NBs", 1, False)
            self.add_experiment_variable("NBs", 128, False)

        self.add_experiment_variable(
            "n_ranks", "{sys_cores_per_node} * {n_nodes}", False
        )
        self.add_experiment_variable(
            "n_threads_per_proc", ["2"], named=True, matrixed=True
        )

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_nodes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "Ns": lambda var, itr, dim, scaling_factor: var.val(dim),
                },
                ScalingMode.Weak: {
                    "n_nodes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "Ns": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
            }
        )

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{Ns}/{n_ranks}",
            total_problem_size="{Ns}",
        )

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"hpl{self.determine_version()}"])
