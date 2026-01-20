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


class Kripke(
    Experiment,
    MpiOnlyExperiment,
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
        default="2025-07",
        values=("develop", "latest", "2025-07", "1.2.7.0"),
        description="app version",
    )

    variant(
        "single_memory",
        default=False,
        description="Enable single memory space model in rocm",
    )

    maintainers("pearce8")

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            # Number of processes in each dimension
            self.add_experiment_variable(
                "n_resources_dict", {"npx": 2, "npy": 2, "npz": 1}, True
            )

            # Per-process size (in zones) in each dimension
            self.add_experiment_variable(
                "total_problem_size_dict", {"nzx": 32, "nzy": 32, "nzz": 16}, True
            )

            self.add_experiment_variable("ngroups", 64, True)
            self.add_experiment_variable("gs", 1, True)
            self.add_experiment_variable("nquad", 128, True)
            self.add_experiment_variable("ds", 128, True)
            self.add_experiment_variable("lorder", 4, True)
        # Must be exec_mode=perf
        else:
            # Number of processes in each dimension
            self.add_experiment_variable(
                "n_resources_dict",
                {"npx": [2, 2, 2], "npy": [2, 2, 2], "npz": [1, 1, 1]},
                True,
            )

            # Per-process size (in zones) in each dimension
            self.add_experiment_variable(
                "total_problem_size_dict",
                {"nzx": [64, 64, 64], "nzy": [64, 64, 64], "nzz": [32, 32, 32]},
                True,
            )

            self.add_experiment_variable("ngroups", [220, 320, 360], True)
            self.add_experiment_variable("gs", 1, True)
            self.add_experiment_variable("nquad", 36, True)
            self.add_experiment_variable("ds", 36, True)
            self.add_experiment_variable("lorder", 4, True)
            self.add_experiment_variable("layout", "GDZ", True)

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{npx}*{npy}*{npz}",
            process_problem_size="({nzx}*{nzy}*{nzz})/({npx}*{npy}*{npz})",
            total_problem_size="{nzx}*{nzy}*{nzz}",
        )

        # In this application, since the input problem sizes (total_problem_size_dict)
        # are global process sizes, strong scaling the problem requires that
        # only n_resources_dict are scaled up, i.e. (x * scaling_factor),
        # total_problem_size_dict remain unchanged

        # For weak scaling, both n_resources_dict and total_problem_size_dict
        # have to be scaled up i.e. (x * scaling_factor)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_resources_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                    "total_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    ),
                },
                ScalingMode.Weak: {
                    "n_resources_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                    "total_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                },
                ScalingMode.Throughput: {
                    "n_resources_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    ),
                    "total_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                },
            }
        )

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        # get package version
        single_memory = (
            "+single_memory"
            if self.spec.variants["single_memory"][0]
            else "~single_memory"
        )
        self.add_package_spec(
            self.name, [f"kripke{self.determine_version()} {single_memory} +mpi"]
        )
