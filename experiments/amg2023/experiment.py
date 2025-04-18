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
from benchpark.new_scaling import NumProcs, ProblemSizes, ScalingMode, UsesPerProcessDomains
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

    def setup_expr_input_variables(self):
        # Number of processes in each dimension
        self.num_procs = NumProcs({"px": 2, "py": 2, "pz": 2})

        # Per-process size (in zones) in each dimension
        self.problem_sizes = ProblemSizes({"nx": 80, "ny": 80, "nz": 80})

    def compute_applications_section(self):
        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_ranks", 'nprocs', True)
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        elif self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", 'nprocs', True)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"amg2023@{app_version} +mpi"])
