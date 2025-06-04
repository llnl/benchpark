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

    @requires_experiment_variables("scaling_factor")
    def strong_scale(self):
        scaling_factor = self.expr_vars.scaling_factor

        num_exprs = int(self.spec.variants["scaling-iterations"][0]) - 1
        var_scaling_factor = int(self.spec.variants["scaling-factor"][0])

        start_dim = scaling_factor.min_dim
        ndims = scaling_factor.ndims

        for itr in range(num_exprs):
            dim = (start_dim + itr) % ndims
            scaling_factor.scale_dim(dim, lambda v: v * var_scaling_factor)

        return []

    def register_required_variables(self):
        self.required_vars.extend(["n_resources", "process_problem_size", "total_problem_size"])

    def compute_applications_section(self):
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            device = "n_gpus"
            n_devices_per_node = "{sys_gpus_per_node}"
        else:
            device = "n_ranks"
            n_devices_per_node = "{sys_cores_per_node}"
            self.add_experiment_variable("n_threads_per_proc", 1)

        self.add_scalar_variable(
            device, f"{n_devices_per_node} * {{scaling_factor}}", True
        )

        self.add_scalar_variable("n_resources", f"{{{device}}}")
        self.add_scalar_variable("process_problem_size", "{zones} / {n_resources}")
        self.add_scalar_variable("total_problem_size", "{zones}")

    def initialize_experiment_variables(self):
        # The total number of resources for this experiment is calculated as:
        # n_devices = n_devices_per_node * scaling_factor
        # Scaling (strong) is achieved by scaling the scaling_factor variable
        # For mpi-only builds:
        # n_devices_per_node = sys_cores_per_node, by default
        # n_devices = n_ranks
        # For gpu builds:
        # n_devices_per_node = sys_gpus_per_node, by default
        # n_devices = n_gpus
        # "zones" defined from mesh file, we are hardcoding it here
        self.add_scalar_variable("zones", 1024, named=True)
        self.add_scalar_variable("scaling_factor", 1, named=False, scalable=True)

    def setup_default_experiment(self):
        pass

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"laghos@{app_version} +metis"])
