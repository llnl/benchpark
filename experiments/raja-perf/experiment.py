# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import Scaling, ScalingMode


class RajaPerf(
    Experiment,
    MpiOnlyExperiment,
    CudaExperiment,
    ROCmExperiment,
    OpenMPExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
    Caliper,
):
    variant(
        "workload",
        default="suite",
        description="base Rajaperf suite or other problem",
    )

    variant(
        "version",
        default="2025.03.0",
        values=("develop", "latest", "2025.03.0", "2024.07.0"),
        description="app version",
    )

    maintainers("michaelmckinsey1")

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            # Per-process size
            self.add_experiment_variable("process_problem_size", 1048576, True)
            # Number of processes
            self.add_experiment_variable("n_resources", 1, False)

        self.set_required_variables(
            total_problem_size="{n_resources}*{process_problem_size}",
        )

        # In this application (RAJAPerf), since the input problem sizes (process_problem_size)
        # are per process sizes, strong scaling the problem implies that
        # as n_resources are scaled up, i.e. (x * scaling_factor),
        # process_problem_size are commensurately scaled down i.e. (x // scaling_factor)

        # For weak scaling, only the n_resources have to be scaled up,
        # process_problem_size remain the same
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_resources": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "process_problem_size": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    // scaling_factor,
                },
                ScalingMode.Weak: {
                    "n_resources": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "process_problem_size": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    ),
                },
                ScalingMode.Throughput: {
                    "n_resources": lambda var, itr, dim, scaling_factor: var.val(dim),
                    "process_problem_size": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                },
            }
        )

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        elif self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_ranks", "{n_resources}", True)
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"raja-perf{self.determine_version()} +mpi"])
