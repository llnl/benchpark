# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import StrongScaling
from benchpark.scaling import WeakScaling
from benchpark.scaling import ThroughputScaling
from benchpark.domaindecomposition import GlobalDomains
from benchpark.caliper import Caliper


@GlobalDomains(
strong_scaling_policy="default",
weak_scaling_policy="default",
throughput_scaling_policy="default",
)
class Kripke(
    Experiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    StrongScaling,
    WeakScaling,
    ThroughputScaling,
    Caliper,
):
    variant(
        "workload",
        default="kripke",
        description="problem1 or problem2",
    )

    variant(
        "version",
        default="develop",
        description="app version",
    )

    maintainers("pearce8")

    def initialize_expr_variables(self):
        expr_input_vars = {
            # Number of processes in each dimension
            "num_procs": {"npx": 2, "npy": 2, "npz": 1},
            # Number of zones in each dimension, per process
            "problem_sizes": {"nzx": 64, "nzy": 64, "nzz": 32},
            "ngroups": 64,
            "gs": 1,
            "nquad": 128,
            "ds": 128,
            "lorder": 4,
        }

        return expr_input_vars

    def compute_strong_scaling_expr_config(self):
        expr_input_vars = self.initialize_expr_variables()
        result = (
            self.apply_strong_scaling_policy({"num_procs" : expr_input_vars["num_procs"]}) | expr_input_vars["problem_sizes"]
        )
        self.add_expr_variables(expr_input_vars, result)

    def compute_weak_scaling_expr_config(self):
        expr_input_vars = self.initialize_expr_variables()
        result = (
            self.apply_weak_scaling_policy({
                "num_procs" : expr_input_vars["num_procs"], 
                "problem_sizes" : expr_input_vars["problem_sizes"], 
            })
        )
        self.add_expr_variables(expr_input_vars, result)

    def compute_throughput_scaling_expr_config(self):
        expr_input_vars = self.initialize_expr_variables()
        result = (
            self.apply_throughput_scaling_policy({"problem_sizes" : expr_input_vars["problem_sizes"]}) | expr_input_vars["num_procs"]
        )
        self.add_expr_variables(expr_input_vars, result)

    def compute_default_expr_config(self):
        expr_input_vars = self.initialize_expr_variables()
        variables = expr_input_vars["num_procs"] | expr_input_vars["problem_sizes"]
        self.add_expr_variables(expr_input_vars, variables)

    def add_expr_variables(self, expr_input_vars, variables):
        for k, v in variables.items():
            self.add_experiment_variable(k, v, True)

        exclude_keys = ["num_procs", "problem_sizes"]
        for k, v in expr_input_vars.items():
            if k not in exclude_keys:
                self.add_experiment_variable(k, v, True)

        n_resources = " * ".join(f"{{{k}}}" for k in expr_input_vars["num_procs"])

        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("n_gpus", n_resources, True)
            self.add_experiment_variable("arch", "CUDA")
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", n_resources, True)
            self.add_experiment_variable("arch", "HIP")
        else:
            if self.spec.satisfies("+openmp"):
                self.add_experiment_variable("n_threads_per_proc", 1, True)
                self.add_experiment_variable("arch", "OpenMP")
            self.add_experiment_variable("n_ranks", n_resources, True)

    def compute_applications_section(self):
        pass

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"kripke@{app_version} +mpi"])
