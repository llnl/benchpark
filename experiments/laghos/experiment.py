# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment


class Laghos(
    Experiment,
    StrongScaling,
    Caliper,
    CudaExperiment,
    ROCmExperiment,
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

    def initialize_expr_variables(self):
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            device_config = {"n_gpus": "{sys_gpus_per_node}"}
        else:
            device_config = {"n_ranks": "{sys_cores_per_node}"}

        return {"device_config": device_config}

    def compute_strong_scaling_expr_config(self):
        # The total number of resources for this experiment is calculated as:
        # n_devices = n_devices_per_node * scaling_factor
        # Scaling (strong) is achieved by scaling the scaling_factor variable
        # For mpi-only builds:
        # n_devices_per_node = sys_cores_per_node, by default
        # n_devices = n_ranks
        # For gpu builds:
        # n_devices_per_node = sys_gpus_per_node, by default
        # n_devices = n_gpus
        expr_vars = self.initialize_expr_variables()
        variables = self.scale_variables([expr_vars["device_config"]])
        self.add_expr_variables(expr_vars, variables)

    def compute_default_expr_config(self):
        expr_vars = self.initialize_expr_variables()
        variables = expr_vars["device_config"]
        self.add_expr_variables(expr_vars, variables)

    def add_expr_variables(self, expr_vars, variables):
        for k, v in variables.items():
            self.add_experiment_variable(k, v, True)

        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("device", "cuda", True)
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("device", "hip", True)

    def compute_applications_section(self):
        pass

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"laghos@{app_version} +metis"])
