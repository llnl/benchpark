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
from benchpark.new_scaling import ScalingMode, UsesPerProcessDomains
from benchpark.caliper import Caliper


class Amg2023(
    Experiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    UsesPerProcessDomains(
        ScalingMode.Strong,
        ScalingMode.Weak,
        ScalingMode.Throughput),
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

    def initialize_experiment_variables(self):
        # Number of processes in each dimension
        self.add_dimensional_variable("num_procs", {"px": 2, "py": 2, "pz": 2}, named=True, scalable=True)

        # Per-process size (in zones) in each dimension
        self.add_dimensional_variable("problem_sizes", {"nx": 80, "ny": 80, "nz": 80}, named=True, scalable=True)

    def setup_default_experiment(self):
        self.add_scalar_variable("nprocs", self.expr_vars.num_procs.prod)
        self.add_scalar_variable("process_problem_size", self.expr_vars.problem_sizes.prod)
        self.add_scalar_variable("total_problem_size", [p*n for p, n in zip(self.expr_vars.num_procs.prod, self.expr_vars.problem_sizes.prod)])

    def compute_applications_section(self):
        if self.spec.satisfies("+openmp"):
            self.add_scalar_variable("n_ranks", "{nprocs}", named=True)
            self.add_scalar_variable("n_threads_per_proc", 1, named=True)
        elif self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_scalar_variable("n_gpus", "{nprocs}", named=True)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"amg2023@{app_version} +mpi"])
