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

    def compute_applications_section(self):
        # "zones" defined from mesh file, we are hardcoding it here
        problem_sizes = {"zones": 1024}

        for nk, nv in problem_sizes.items():
            self.add_experiment_variable(nk, nv, True)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            device = "n_gpus"
            n_devices_per_node = "{sys_gpus_per_node}"
        else:
            device = "n_ranks"
            n_devices_per_node = "{sys_cores_per_node}"
            self.add_experiment_variable("n_threads_per_proc", 1)

        # The total number of resources for this experiment is calculated as:
        # n_devices = n_devices_per_node * scaling_factor
        # Scaling (strong) is achieved by scaling the scaling_factor variable
        # For mpi-only builds:
        # n_devices_per_node = sys_cores_per_node, by default
        # n_devices = n_ranks
        # For gpu builds:
        # n_devices_per_node = sys_gpus_per_node, by default
        # n_devices = n_gpus
        scaling_factor = {"scaling_factor": 1}

        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("device", "cuda", True)
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("device", "hip", True)

        if self.spec.satisfies("+single_node"):
            for pk, pv in scaling_factor.items():
                self.add_experiment_variable(pk, pv)
        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(scaling_factor.keys()): list(scaling_factor.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv)

        self.add_experiment_variable(
            device, f"{n_devices_per_node} * {{scaling_factor}}", True
        )

        n_resources = "{" + str(device) + "}"
        self.set_required_variables(
            n_resources=n_resources,
            process_problem_size="{zones}/" + n_resources,
            total_problem_size="{zones}",
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"laghos@{app_version} +metis"])
