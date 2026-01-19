# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.scaling import Scaling, ScalingMode


class Genesis(
    Experiment,
    MpiOnlyExperiment,
    OpenMPExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
):

    variant(
        "workload",
        default="DHFR",
        values=("DHFR", "ApoA1", "UUN", "cryoEM"),
        description="genesis",
    )

    variant(
        "version",
        default="2.1.6",
        values=("2.1.6", "main"),
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
            self.add_experiment_variable("n_nodes", ["1"], True)
            self.add_experiment_variable(
                "total_problem_size_dict", {"lx": 32, "ly": 6, "lz": 4}, True
            )
            self.add_experiment_variable("lt", "3")
            self.add_experiment_variable(
                "n_resources_dict", {"px": 1, "py": 1, "pz": 1}, True
            )
            self.add_experiment_variable("pt", "1")
        # Must be exec_mode=perf
        else:
            self.add_experiment_variable("n_nodes", ["2"], True)
            # Per-process size (in zones) in each dimension
            self.add_experiment_variable(
                "total_problem_size_dict",
                {"lx": [32, 32, 32], "ly": [6, 6, 6], "lz": [4, 4, 4]},
                True,
            )
            self.add_experiment_variable("lt", "3")
            # Number of processes in each dimension
            self.add_experiment_variable(
                "n_resources_dict",
                {"px": [1, 1, 1], "py": [1, 1, 1], "pz": [1, 1, 1]},
                True,
            )
            self.add_experiment_variable("pt", "1")

        self.set_required_variables(
            n_resources="{px}*{py}*{pz}",
            process_problem_size="{lx}*{ly}*{lz}/{px}*{py}*{pz}",
            total_problem_size="{lx}*{ly}*{lz}",
        )

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

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"genesis{self.determine_version()}"])
