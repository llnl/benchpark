# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment, requires_experiment_variables
from benchpark.scaling import StrongScaling
from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.new_scaling import Scaling, ScalingMode


class Laghos(
    Experiment,
    CudaExperiment,
    ROCmExperiment,
    Scaling(
        ScalingMode.Strong,
    ),
    Caliper,
):

    variant(
        "workload",
        default="triplept",
        description="triplept or other problem",
    )

    variant(
        "version",
        default="develop",
        description="app version",
    )

    maintainers("wdhawkins")

    @requires_experiment_variables("device_scaling_factor")
    def strong_scale(self):
        device_scaling_factor = self.expr_vars.device_scaling_factor

        num_exprs = int(self.spec.variants["scaling-iterations"][0]) - 1
        scaling_factor = int(self.spec.variants["scaling-factor"][0])

        start_dim = device_scaling_factor.min_dim
        ndims = device_scaling_factor.ndims

        for itr in range(num_exprs):
            dim = (start_dim + itr) % ndims
            device_scaling_factor.scale_dim(dim, lambda v: v * scaling_factor)

        return None

    def initialize_experiment_variables(self):
        # The total number of resources for this experiment is calculated as:
        # n_devices = n_devices_per_node * device_scaling_factor
        # Scaling (strong) is achieved by scaling the device_scaling_factor variable
        # For mpi-only builds:
        # n_devices_per_node = sys_cores_per_node, by default
        # n_devices = n_ranks
        # For gpu builds:
        # n_devices_per_node = sys_gpus_per_node, by default
        # n_devices = n_gpus
        self.add_scalar_variable("device_scaling_factor", 1, named=True, scalable=True)

    def setup_default_experiment(self):
        pass

    def compute_applications_section(self):
        if self.spec.satisfies("+cuda"):
            self.add_scalar_variable(
                "n_gpus", "{sys_gpus_per_node} * {device_scaling_factor}", True
            )
            self.add_scalar_variable("device", "cuda", named=True)
        elif self.spec.satisfies("+rocm"):
            self.add_scalar_variable(
                "n_gpus", "{sys_gpus_per_node} * {device_scaling_factor}", True
            )
            self.add_scalar_variable("device", "hip", named=True)
        else:
            device = "n_ranks"
            n_devices_per_node = "{sys_cores_per_node}"
            self.add_scalar_variable(
                "n_ranks", "{sys_cores_per_node} * {device_scaling_factor}", True
            )
            self.add_scalar_variable("n_threads_per_proc", 1)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"laghos@{app_version} +metis"])
