# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.new_scaling import ScalingMode, Scaling
from benchpark.caliper import Caliper


class Kripke(
    Experiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
    Caliper,
):
    variant(
        "workload",
        default="kripke",
        values=("kripke",),
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
        self.add_experiment_variable("num_procs", {"npx": 2, "npy": 2, "npz": 1}, True)

        # Per-process size (in zones) in each dimension
        self.add_experiment_variable(
            "problem_sizes", {"nzx": 64, "nzy": 64, "nzz": 32}, True
        )

        self.add_experiment_variable("ngroups", 64, True)
        self.add_experiment_variable("gs", 1, True)
        self.add_experiment_variable("nquad", 128, True)
        self.add_experiment_variable("ds", 128, True)
        self.add_experiment_variable("lorder", 4, True)

        # Register the scaling variables and their respective scaling functions
        # required to correctly scale the experiment for the given scaliing policy
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "num_procs": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "problem_sizes": lambda var, itr, dim, scaling_factor: var.val(dim),
                },
                ScalingMode.Weak: {
                    "num_procs": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "problem_sizes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
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
            n_resources="{npx}*{npy}*{npz}",
            process_problem_size="{nzx}*{nzy}*{nzz}/({npx}*{npy}*{npz})",
            total_problem_size="{nzx}*{nzy}*{nzz}",
        )

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("arch", "OpenMP")
        elif self.spec.satisfies("+cuda"):
            self.add_experiment_variable("arch", "CUDA")
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("arch", "HIP")
        else:
            self.add_experiment_variable("arch", "Sequential")

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"kripke@{app_version} +mpi"])
