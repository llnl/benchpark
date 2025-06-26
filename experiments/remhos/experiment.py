# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment


class Remhos(
    Experiment,
    StrongScaling,
    Caliper,
    CudaExperiment,
    ROCmExperiment,
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
        # TODO: Replace with conflicts clause
        scaling_modes = {
            "strong": self.spec.satisfies("+strong"),
            "single_node": self.spec.satisfies("+single_node"),
        }

        scaling_mode_enabled = [key for key, value in scaling_modes.items() if value]
        if len(scaling_mode_enabled) != 1:
            print(scaling_mode_enabled)
            raise BenchparkError(
                f"Only one type of scaling per experiment is allowed for application package {self.name}"
            )

        if self.spec.variants["workload"][0] == "2d":
            problem_sizes = {"epm": 1024}
        elif self.spec.variants["workload"][0] == "3d":
            problem_sizes = {"epm": 512}
        device = "n_ranks"

        for nk, nv in problem_sizes.items():
            self.add_experiment_variable(nk, nv, True)

        scaling_factor = {"scaling_factor": 1}

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            device = "n_gpus"
            n_devices_per_node = "{sys_gpus_per_node}"
        else:
            device = "n_ranks"
            n_devices_per_node = "{sys_cores_per_node}"
            self.add_experiment_variable("n_threads_per_proc", 1)

        if self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(scaling_factor.keys()): list(scaling_factor.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv, True)
        else:
            for pk, pv in scaling_factor.items():
                self.add_experiment_variable(pk, pv, True)

        self.add_experiment_variable(
            device, f"{n_devices_per_node}*" + "{scaling_factor}", True
        )

        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("device", "cuda")
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("device", "hip")
        else:
            self.add_experiment_variable("device", "cpu")

        n_resources = "{" + device + "}"
        self.set_required_variables(
            n_resources=n_resources,
            process_problem_size="{epm}",
            total_problem_size="{epm}*" + n_resources,
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"remhos@{app_version} +metis"])
