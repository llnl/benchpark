# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
from benchpark.scaling import WeakScaling


class Ior(
    Experiment,
    StrongScaling,
    WeakScaling,
):
    variant(
        "workload",
        default="ior",
        description="base IOR  or other problem",
    )

    variant(
        "version",
        default="4.0.0",
        values=("develop", "latest", "4.0.0"),
        description="app version",
    )

    maintainers("hariharan-devarajan")

    def compute_applications_section(self):
        # TODO: Replace with conflicts clause
        scaling_modes = {
            "strong": self.spec.satisfies("+strong"),
            "weak": self.spec.satisfies("+weak"),
            "single_node": self.spec.satisfies("+single_node"),
        }

        scaling_mode_enabled = [key for key, value in scaling_modes.items() if value]
        if len(scaling_mode_enabled) != 1:
            raise BenchparkError(
                f"Only one type of scaling per experiment is allowed for application package {self.name}"
            )

        num_nodes = {"n_nodes": 1}
        t = "{b}/256"
        self.add_experiment_variable("t", t, True)

        if self.spec.satisfies("+single_node"):
            for pk, pv in num_nodes.items():
                self.add_experiment_variable(pk, pv, True)
            self.add_experiment_variable("b", "268435456", True)
        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)
            # 256 mb
            self.add_experiment_variable("b", "268435456 / {n_nodes}", True)
        elif self.spec.satisfies("+weak"):
            scaled_variables = self.generate_weak_scaling_params(
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)

            self.add_experiment_variable("b", "268435456", True)

        self.add_experiment_variable("t", t, True)
        self.add_experiment_variable(
            "n_ranks", "{sys_cores_per_node} * {n_nodes}", True
        )

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{b}/{n_ranks}",
            total_problem_size="{b}",
        )

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"ior{self.determine_version()}"])
