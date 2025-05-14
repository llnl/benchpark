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
from benchpark.caliper import Caliper


class RajaPerf(
    Experiment,
    StrongScaling,
    CudaExperiment,
    ROCmExperiment,
    OpenMPExperiment,
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
        elif self.spec.satisfies("+strong"):
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

        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("variant", "Base_CUDA", True)
            self.add_experiment_variable("tuning", "block_256", True)
            self.add_experiment_variable("n_gpus", n_resources, True)
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("variant", "Base_HIP", True)
            self.add_experiment_variable("tuning", "block_256", True)
            self.add_experiment_variable("n_gpus", n_resources, True)
        elif self.spec.satisfies("+openmp"):
            self.add_experiment_variable("variant", "Base_OpenMP", True)
            self.add_experiment_variable("tuning", "default", True)
            self.add_experiment_variable("n_ranks", n_resources, True)
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        else:
            self.add_experiment_variable("variant", "Base_Seq", True)
            self.add_experiment_variable("tuning", "default", True)
            self.add_experiment_variable("n_ranks", n_resources, True)

        self.add_experiment_variable("n_resources", "{n_ranks}", False)
        self.add_experiment_variable("process_problem_size", "{size}", False)
        self.add_experiment_variable("total_problem_size", "{n_ranks}*{size}", False)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"raja-perf@{app_version}"])
