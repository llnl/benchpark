# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.scaling import Scaling, ScalingMode


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
        description="Which ramble workload to execute.",
    )

    variant(
        "version",
        default="2.3-caliper",
        values=("latest", "2.3-caliper", "2.3", "2.2"),
        description="Which benchmark version to use.",
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
        # Must be exec_mode=perf if not test mode.
        else:
            self.add_experiment_variable("n_nodes", 16, True)
            self.add_experiment_variable("Ns", 100000, True)
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

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{Ns}/{n_ranks}",
            total_problem_size="{Ns}",
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

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"hpl{self.determine_version()}"])
