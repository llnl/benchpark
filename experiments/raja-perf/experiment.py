# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

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

    def initialize_expr_variables(self):
        return {"num_procs": {"np": 1}}

    def compute_strong_scaling_expr_config(self):
        expr_vars = self.initialize_expr_variables()
        variables = self.scale_variables([expr_vars["num_procs"]])
        self.add_expr_variables(expr_vars, variables)

    def compute_default_expr_config(self):
        expr_vars = self.initialize_expr_variables()
        variables = expr_vars["num_procs"]
        self.add_expr_variables(expr_vars, variables)

    def compute_applications_section(self):
        pass

    def add_expr_variables(self, expr_vars, variables):
        for k, v in variables.items():
            self.add_experiment_variable(k, v, True)

        exclude_keys = ["num_procs"]
        for k, v in expr_vars.items():
            if k not in exclude_keys:
                self.add_experiment_variable(k, v, True)

        n_resources = " * ".join(f"{{{k}}}" for k in expr_vars["num_procs"])

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", n_resources, True)
        else:
            if self.spec.satisfies("+openmp"):
                self.add_experiment_variable("n_threads_per_proc", 1, True)
            self.add_experiment_variable("n_ranks", n_resources, True)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"raja-perf@{app_version}"])
