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


class Hpcg(
    Experiment,
    MpiOnlyExperiment,
    OpenMPExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak),
    Caliper,
):

    variant(
        "workload",
        default="standard",
        description="workload to run",
    )
    variant(
        "version",
        default="caliper",
        values=("3.1", "develop", "caliper"),
        description="app version",
    )

    maintainers("pearce8")

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            self.add_experiment_variable(
                "problem_sizes", {"mx": 104, "my": 104, "mz": 104}, True
            )
            self.add_experiment_variable("num_procs", 1, True)

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
            }
        )

        self.add_experiment_variable("n_ranks", "{num_procs}", True)
        self.add_experiment_variable("n_threads_per_proc", 1, True)
        self.add_experiment_variable("matrix_size", "{mx} {my} {mz}", False)

        self.add_experiment_variable("iterations", "60", False)

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{mx}*{my}*{mz}/{n_ranks}",
            total_problem_size="{mx}*{my}*{mz}",
        )

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"hpcg{self.determine_version()}"])
