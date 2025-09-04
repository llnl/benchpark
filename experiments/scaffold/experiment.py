# Copyright 2024 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
from benchpark.rocm import ROCmExperiment
from benchpark.caliper import Caliper


class Scaffold(
    Experiment,
    StrongScaling,
    ROCmExperiment,
    Caliper,
):

    maintainers("michaelmckinsey1")

    variant(
        "workload",
        default="sweep",
        values=("sweep",),
    )

    variant(
        "scaffold_path",
        default=" ",
        description="Path to local repository of ScaFFold (i.e. git clone), since it is private.",
    )

    variant("version", default="develop", description="app version")

    def compute_applications_section(self):
        # TODO: Replace with conflicts clause
        scaling_modes = {
            "strong": self.spec.satisfies("+strong"),
            "weak": self.spec.satisfies("+weak"),
            "throughput": self.spec.satisfies("+throughput"),
            "single_node": self.spec.satisfies("+single_node"),
        }

        scaling_mode_enabled = [key for key, value in scaling_modes.items() if value]
        if len(scaling_mode_enabled) != 1:
            raise BenchparkError(
                f"Only one type of scaling per experiment is allowed for application package {self.name}"
            )

        self.add_experiment_variable(
            "package_path", self.spec.variants["scaffold_path"][0], False
        )
        self.add_experiment_variable("timeout", 720, True)

        problem_sizes = {"problem_scale": 6}

        for nk, nv in problem_sizes.items():
            self.add_experiment_variable(nk, nv, True)

        if self.spec.satisfies("+rocm"):
            n_resources = {"n_gpus": 4}

        if self.spec.satisfies("+single_node"):
            for pk, pv in n_resources.items():
                self.add_experiment_variable(pk, pv, True)
        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(n_resources.keys()): list(n_resources.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv, True)

        self.set_required_variables(
            n_resources="{n_gpus}",
            process_problem_size="{problem_scale}/{n_gpus}",
            total_problem_size="{problem_scale}",
        )

    def compute_package_section(self):
        # Spec written into requirements.txt for pip install
        self.add_package_spec(
            self.name,
            [
                "--extra-index-url https://download.pytorch.org/whl/\n{package_path}"
            ],
        )
