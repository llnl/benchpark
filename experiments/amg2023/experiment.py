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
from benchpark.new_scaling import ScalingMode, Scaling
from benchpark.caliper import Caliper


class Amg2023(
    Experiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
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

    def compute_applications_section(self):
        # Number of processes in each dimension
        self.add_experiment_variable("num_procs", {"px": 2, "py": 2, "pz": 2}, True)

        # Per-process size (in zones) in each dimension
        self.add_experiment_variable(
            "problem_sizes", {"nx": 80, "ny": 80, "nz": 80}, True
        )

        # Register the scaling variables and their respective scaling functions
        # required to correctly scale the experiment for the given scaliing policy
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "num_procs": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "problem_sizes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    // scaling_factor,
                },
                ScalingMode.Weak: {
                    "num_procs": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "problem_sizes": lambda var, itr, dim, scaling_factor: var.val(dim),
                },
                ScalingMode.Throughput: {
                    "num_procs": lambda var, itr, dim, scaling_factor: var.val(dim),
                    "problem_sizes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
            }
        )

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{px}*{py}*{pz}",
            process_problem_size="{nx}*{ny}*{nz}",
            total_problem_size="{nx}*{ny}*{nz}*{px}*{py}*{pz}",
        )

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"amg2023@{app_version} +mpi"])
