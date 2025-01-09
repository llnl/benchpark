# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
from benchpark.expr.builtin.caliper import Caliper
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

    def compute_applications_section(self):

        # Number of initial nodes
        n_resources = {"n_nodes": 1}
        device = "n_ranks"
        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("device", "cuda", True)
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("device", "hip", True)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            device = "n_gpus"
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

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        system_specs["lapack"] = "default-lapack"
        system_specs["blas"] = "default-blas"

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
        self.add_spack_spec(system_specs["mpi"])

        self.add_spack_spec(
            self.name, [f"laghos@{app_version} +metis", system_specs["compiler"]]
        )
