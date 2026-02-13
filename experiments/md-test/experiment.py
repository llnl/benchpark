# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.scaling import Scaling, ScalingMode


class MdTest(
    Experiment,
    MpiOnlyExperiment,
    Scaling(ScalingMode.Strong),
):
    variant(
        "workload",
        default="multi-file",
        description="base md-test or other problem",
    )

    variant(
        "version",
        default="1.9.3",
        description="app version",
    )

    maintainers("rfhaque")

    def compute_applications_section(self):

        num_resources = {"n_ranks": 1}

        self.add_experiment_variable("num-objects", "1000", True)
        self.add_experiment_variable("iterations", "10", True)

        if self.spec.satisfies("exec_mode=test"):
            for pk, pv in num_resources.items():
                self.add_experiment_variable(pk, pv, True)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_ranks": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "num-objects": lambda var, itr, dim, scaling_factor: var.val(dim),
                },
            }
        )

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{num-objects}/{n_ranks}",
            total_problem_size="{num-objects}",
        )

    def compute_package_section(self):
        self.add_package_spec(
            "ior",
            [
                "ior@3.3.0",
            ],
        )
        self.add_package_spec(self.name, [f"mdtest{self.determine_version()}"])
