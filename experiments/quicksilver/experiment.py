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


class Quicksilver(
    Experiment,
    MpiOnlyExperiment,
    OpenMPExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak),
    Caliper,
):
    variant(
        "workload",
        default="quicksilver",
        description="quicksilver",
    )

    variant(
        "version",
        default="caliper",
        values=("master", "caliper"),
        description="app version",
    )

    maintainers("rfhaque")

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            self.add_experiment_variable(
                "n_resources_dict", {"I": 2, "J": 2, "K": 1}, True
            )

            self.add_experiment_variable(
                "total_problem_size_dict", {"X": 16, "Y": 16, "Z": 8}, True
            )
        else:
            self.add_experiment_variable(
                "n_resources_dict", {"I": 2, "J": 2, "K": 1}, True
            )

            self.add_experiment_variable(
                "total_problem_size_dict", {"X": 32, "Y": 32, "Z": 16}, True
            )

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_resources_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                    "total_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    ),
                },
                ScalingMode.Weak: {
                    "n_resources_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                    "total_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                },
            }
        )

        self.add_experiment_variable("n", "{x}*{y}*{z}*10")
        self.add_experiment_variable("x", "{X}")
        self.add_experiment_variable("y", "{Y}")
        self.add_experiment_variable("z", "{Z}")

        self.set_required_variables(
            n_resources="{I}*{J}*{K}",
            process_problem_size="{n}/{n_resources}",
            total_problem_size="{n}",
        )

        self.add_experiment_variable("n_threads_per_proc", "1")
        self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"quicksilver{self.determine_version()}"])
