# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.scaling import Scaling, ScalingMode


class Qws(
    Experiment,
    MpiOnlyExperiment,
    OpenMPExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
    Caliper,
):

    variant(
        "workload",
        default="qws",
        description="qws",
    )

    variant(
        "version",
        default="master",
        description="app version",
    )

    maintainers("jdomke", "SBA0486")

    def compute_applications_section(self):
        self.add_experiment_variable("experiment_setup", "")
        self.add_experiment_variable("tol_outer", "-1")
        self.add_experiment_variable("tol_inner", "-1")
        self.add_experiment_variable("maxiter_plus1_outer", "6")
        self.add_experiment_variable("maxiter_inner", "50")

        if self.spec.satisfies("exec_mode=test"):
            self.add_experiment_variable(
                "process_problem_size_dict",
                {"lx": 32, "ly": 6, "lz": 4, "lt": 2},
                True,
            )
            self.add_experiment_variable(
                "n_resources_dict", {"px": 1, "py": 1, "pz": 1, "pt": 1}, True
            )
        # Must be exec_mode=perf
        else:
            # Per-process size (in zones) in each dimension
            self.add_experiment_variable(
                "process_problem_size_dict",
                {"lx": 64, "ly": 12, "lz": 8, "lt": 2},
                True,
            )
            # Number of processes in each dimension
            self.add_experiment_variable(
                "n_resources_dict", {"px": 2, "py": 2, "pz": 2, "pt": 1}, True
            )

        self.set_required_variables(
            n_resources="{px}*{py}*{pz}*{pt}",
            process_problem_size="({lx}*{ly}*{lz}*{lt})",
            total_problem_size="{lx}*{ly}*{lz}*{lt}*{px}*{py}*{pz}*{pt}",
        )

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_resources_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                    "process_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    // scaling_factor,
                },
                ScalingMode.Weak: {
                    "n_resources_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                    "process_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    ),
                },
                ScalingMode.Throughput: {
                    "n_resources_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    ),
                    "process_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                },
            }
        )

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"qws{self.determine_version()}"])
