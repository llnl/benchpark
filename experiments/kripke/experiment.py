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
from benchpark.new_scaling import ScalingMode, UsesGlobalDomains
from benchpark.caliper import Caliper


class Kripke(
    Experiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    UsesGlobalDomains(
        ScalingMode.Strong,
        ScalingMode.Weak,
        ScalingMode.Throughput
    ),
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

    def initialize_experiment_variables(self):
        # Number of processes in each dimension
        self.add_dimensional_variable("num_procs", {"npx": 2, "npy": 2, "npz": 2}, named=True, scalable=True)

        # Per-process size (in zones) in each dimension
        self.add_dimensional_variable("problem_sizes", {"nzx": 80, "nzy": 80, "nzz": 80}, named=True, scalable=True)

        self.add_scalar_variable("ngroups", 64, named=True)
        self.add_scalar_variable("gs", 1, named=True)
        self.add_scalar_variable("nquad", 128, named=True)
        self.add_scalar_variable("ds", 128, named=True)
        self.add_scalar_variable("lorder", 4, named=True)

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

        if self.spec.satisfies("+openmp"):
            self.add_scalar_variable("arch", "OpenMP")
        elif self.spec.satisfies("+cuda"):
            self.add_scalar_variable("arch", "CUDA")
        elif self.spec.satisfies("+rocm"):
            self.add_scalar_variable("arch", "HIP")

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"kripke@{app_version} +mpi"])
