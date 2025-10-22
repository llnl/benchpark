# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import Scaling, ScalingMode


class Remhos(
    Experiment,
    MpiOnlyExperiment,
    CudaExperiment,
    ROCmExperiment,
    Scaling(ScalingMode.Strong),
    Caliper,
):

    variant(
        "workload",
        default="2d",
        values=("2d", "3d"),
        description="2d or 3d run",
    )

    variant(
        "version",
        default="gpu-opt",
        values=("develop", "latest", "gpu-fom", "gpu-opt", "1.0"),
        description="app version",
    )

    maintainers("rfhaque")

    def compute_applications_section(self):
        if self.spec.variants["workload"][0] == "2d":
            self.add_experiment_variable("epm", 1024, False)
        elif self.spec.variants["workload"][0] == "3d":
            self.add_experiment_variable("epm", 512, False)

        # resource_count is the number of resources used for this experiment:
        self.add_experiment_variable("resource_count", 1, False)

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{resource_count}",
            process_problem_size="{epm}",
            total_problem_size="{epm} * {n_resources}",
        )

        # Register the scaling variables and their respective scaling functions
        # required to correctly scale the experiment for the given scaliing policy
        # Strong scaling scales up resource_count by the specified scaling_factor
        # and scales epm down by scaling_factor to keep the problem size constant
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "resource_count": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "epm": lambda var, itr, dim, scaling_factor: var.val(dim)
                    // scaling_factor,
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
        self.add_package_spec(self.name, [f"remhos{self.determine_version()} +metis"])
