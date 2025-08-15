# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.new_scaling import ScalingMode, Scaling


class Ior(
    Experiment,
    MpiOnlyExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak)
):
    variant(
        "workload",
        default="ior",
        description="base IOR  or other problem",
    )

    variant(
        "version",
        default="3.3.0",
        description="app version",
    )

    maintainers("hariharan-devarajan")

    def compute_applications_section(self):
        num_nodes = {"n_nodes": 1}
        t = "{b}/256"
        self.add_experiment_variable("t", t, True)

        if self.spec.satisfies("exec_mode=test"):
            for pk, pv in num_nodes.items():
                self.add_experiment_variable(pk, pv, True)
            self.add_experiment_variable("b", "268435456", True)

        self.add_experiment_variable("t", t, True)
        self.add_experiment_variable(
            "n_ranks", "{sys_cores_per_node} * {n_nodes}", True
        )

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_ranks": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "b": lambda var, itr, dim, scaling_factor: var.val(dim),
                },
                ScalingMode.Weak: {
                    "n_ranks": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "b": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
            }
        )

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{b}/{n_ranks}",
            total_problem_size="{b}",
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"ior@{app_version}"])
