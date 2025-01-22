# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
from benchpark.expr.builtin.caliper import Caliper
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

        n_resources = {"n_nodes": 8}
        # problem_size = {"epm": 512}
        device = "n_ranks"

        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("device", "cuda", True)
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("device", "hip", True)
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            device = "n_gpus"
        else:
            self.add_experiment_variable(
                "n_ranks", "{sys_cores_per_node} * {n_nodes}", True
            )
            self.add_experiment_variable("device", "cpu", True)

        if self.spec.satisfies("+single_node"):
            for pk, pv in n_resources.items():
                self.add_experiment_variable(device, pv, True)

        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(n_resources.keys()): list(n_resources.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv, True)
            num_resources = scaled_variables["n_nodes"]
            self.add_experiment_variable(device, num_resources, True)
        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("arch", "CUDA")
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("arch", "HIP")

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        system_specs["blas"] = "blas"
        system_specs["lapack"] = "lapack"

        # set package spack specs
        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["mpi"])

        if self.spec.satisfies("+cuda"):
            system_specs["cuda_version"] = "{default_cuda_version}"
            system_specs["cuda_arch"] = "{cuda_arch}"
        elif self.spec.satisfies("+rocm"):
            system_specs["rocm_arch"] = "{rocm_arch}"

        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["blas"])
        self.add_spack_spec(system_specs["lapack"])

        self.add_spack_spec(
            self.name, [f"remhos@{app_version} +metis", system_specs["compiler"]]
        )
