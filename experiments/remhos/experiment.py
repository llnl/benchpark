# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.new_scaling import Scaling, ScalingMode


class Remhos(
    Experiment,
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
        values=("1.0", "develop", "gpu-fom", "gpu-opt"),
        description="app version",
    )

    maintainers("rfhaque")

    def compute_applications_section(self):
        if self.spec.variants["workload"][0] == "2d":
            self.add_experiment_variable("epm", 1024, False)
        elif self.spec.variants["workload"][0] == "3d":
            self.add_experiment_variable("epm", 512, False)

        # The total number of resources for this experiment is calculated as:
        # n_devices = n_devices_per_node * scaling_factor
        # Scaling (strong) is achieved by scaling the scaling_factor variable
        # For mpi-only builds:
        # n_devices_per_node = sys_cores_per_node, by default
        # n_devices = n_ranks
        # For gpu builds:
        # n_devices_per_node = sys_gpus_per_node, by default
        # n_devices = n_gpus
        self.add_experiment_variable("scaling_factor", 1, False)

        # Register the scaling variables and their respective scaling functions
        # required to correctly scale the experiment for the given scaliing policy
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "scaling_factor": lambda var, itr, dim, scaling_factor: var.val(dim)
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
            device = "n_gpus"
            n_devices_per_node = "{sys_gpus_per_node}"
        else:
            device = "n_ranks"
            n_devices_per_node = "{sys_cores_per_node}"
            self.add_experiment_variable("n_threads_per_proc", 1)

        self.add_experiment_variable(
            device, f"{n_devices_per_node} * {{scaling_factor}}", True
        )

        self.set_required_variables(
            n_resources=f"{{{device}}}",
            process_problem_size="{epm}",
            total_problem_size="{epm} * {n_resources}",
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"remhos@{app_version} +metis"])
