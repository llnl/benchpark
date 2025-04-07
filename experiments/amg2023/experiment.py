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
from benchpark.domaindecomposition import PerProcessDomains
from benchpark.caliper import Caliper

@PerProcessDomains(
strong_scaling_policy="conserveglobalproblemsize",
weak_scaling_policy="default",
throughput_scaling_policy="default",
)
class Amg2023(
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
        default="problem1",
        values=("problem1", "problem2"),
        description="problem1 or problem2",
    )

    variant(
        "version",
        default="develop",
        description="app version",
    )

    maintainers("pearce8")

    # requires("system+papi", when(caliper=topdown*))

    # TODO: Support list of 3-tuples
    # variant(
    #     "p",
    #     description="value of p",
    # )

    # TODO: Support list of 3-tuples
    # variant(
    #     "n",
    #     description="value of n",
    # )

    def initialize_expr_variables(self):
        expr_input_vars = {
            # Number of processes in each dimension
            "num_procs": {"px": 2, "py": 2, "pz": 2},
            # Per-process size (in zones) in each dimension
            "problem_sizes": {"nx": 80, "ny": 80, "nz": 80},
        }

        return expr_input_vars

    def compute_strong_scaling_expr_config(self):
        expr_input_vars = self.initialize_expr_variables()
        result = self.apply_strong_scaling_policy(expr_input_vars)
        self.add_expr_variables(expr_input_vars, result)

    def compute_weak_scaling_expr_config(self):
        expr_input_vars = self.initialize_expr_variables()
        result = (
            self.apply_weak_scaling_policy({"num_procs" : expr_input_vars["num_procs"]}) | expr_input_vars["problem_sizes"]
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

        n_resources = " * ".join(f"{{{k}}}" for k in expr_input_vars["num_procs"])

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", n_resources, True)
        else:
            if self.spec.satisfies("+openmp"):
                self.add_experiment_variable("n_threads_per_proc", 1, True)
            self.add_experiment_variable("n_ranks", n_resources, True)

    def compute_applications_section(self):
        pass

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"amg2023@{app_version} +mpi"])
