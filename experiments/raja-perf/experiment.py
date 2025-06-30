# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import ThroughputScaling
from benchpark.caliper import Caliper


class RajaPerf(
    Experiment,
    StrongScaling,
    CudaExperiment,
    ROCmExperiment,
    OpenMPExperiment,
    ThroughputScaling,
    Caliper,
):
    variant(
        "workload",
        default="suite",
        description="base Rajaperf suite or other problem",
    )

    variant(
        "version",
        default="develop",
        values=("develop", "2025.03.0", "2024.07.0"),
        description="app version",
    )

    maintainers("michaelmckinsey1")

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

        n_resources = {"n_ranks": 1}
        problem_sizes = {"size": 1048576}

        if self.spec.satisfies("+single_node"):
            for pk, pv in n_resources.items():
                n_resources = pv
            for nk, nv in problem_sizes.items():
                self.add_experiment_variable(nk, nv, True)
        elif self.spec.satisfies("+weak"):
            # Use "strong scaling" to generate resource scaling since problem size is per-process
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(n_resources.keys()): list(n_resources.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            n_resources = scaled_variables["n_ranks"]
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv, True)
            for nk, nv in problem_sizes.items():
                self.add_experiment_variable(nk, nv, True)
        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(n_resources.keys()): list(n_resources.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            n_resources = scaled_variables["n_ranks"]
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv, True)
            # Notice 1/scaling-factor to keep total problem size constant for per-process problem size experiments
            scaled_problem_sizes = self.generate_strong_scaling_params(
                {tuple(problem_sizes.keys()): list(problem_sizes.values())},
                1 / int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            problem_sizes = scaled_problem_sizes["size"]
            for nk, nv in scaled_problem_sizes.items():
                self.add_experiment_variable(nk, nv, True)
        elif self.spec.satisfies("+throughput"):
            scaled_variables = self.generate_throughput_scaling_params(
                {tuple(problem_sizes.keys()): list(problem_sizes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            n_resources = n_resources["n_ranks"]
            for nk, nv in scaled_variables.items():
                self.add_experiment_variable(nk, nv, True)

        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("n_gpus", n_resources, True)
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", n_resources, True)
        elif self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_ranks", n_resources, True)
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        else:
            self.add_experiment_variable("n_ranks", n_resources, True)

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{size}",
            total_problem_size="{n_ranks}*{size}",
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"raja-perf@{app_version}"])
