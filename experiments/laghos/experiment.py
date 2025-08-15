# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.new_scaling import Scaling, ScalingMode


class Laghos(
    Experiment,
    MpiOnlyExperiment,
    CudaExperiment,
    ROCmExperiment,
    Scaling(ScalingMode.Strong),
    Caliper,
):

    variant(
        "workload",
        default="triplept",
        description="triplept or other problem",
    )

    variant(
        "version",
        default="caliper",
        description="app version",
    )

    maintainers("wdhawkins")

    def compute_applications_section(self):
        # "zones" defined from mesh file, we are hardcoding it here
        self.add_experiment_variable("zones", 1024, True)

        # resource_count is the number of resources used for this experiment:
        self.add_experiment_variable("resource_count", 1, False)

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{resource_count}",
            process_problem_size="{zones} / {n_resources}",
            total_problem_size="{zones}",
        )

        # Register the scaling variables and their respective scaling functions
        # required to correctly scale the experiment for the given scaliing policy
        # Strong scaling scales up resource_count by the specified scaling_factor
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "resource_count": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
            }
        )

        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("device", "cuda", True)
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("device", "hip", True)
        else:
            self.add_experiment_variable("device", "cpu", True)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"laghos{self.determine_version()} +metis"])
