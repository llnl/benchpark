# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import StrongScaling
from benchpark.scaling import WeakScaling
from benchpark.caliper import Caliper


class Branson(
    Experiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    StrongScaling,
    WeakScaling,
    Caliper,
):
    variant(
        "workload",
        default="branson",
        description="workload name",
    )

    variant(
        "version",
        default="develop",
        description="app version",
    )

    variant(
        "n_groups",
        default="30",
        values=int,
        description="Number of groups",
    )

    def compute_applications_section(self):
        # TODO: Replace with conflicts clause
        scaling_modes = {
            "strong": self.spec.satisfies("+strong"),
            "weak": self.spec.satisfies("+weak"),
            "single_node": self.spec.satisfies("+single_node"),
        }

        scaling_mode_enabled = [key for key, value in scaling_modes.items() if value]
        if len(scaling_mode_enabled) != 1:
            raise BenchparkError(
                f"Only one type of scaling per experiment is allowed for application package {self.name}"
            )

        # Number of processes in each dimension
        num_nodes = {"n_nodes": 1}

        # Per-process size (in zones) in each dimension
        num_particles = {"num_particles": 850000000}

        if self.spec.satisfies("+single_node"):
            for pk, pv in num_nodes.items():
                self.add_experiment_variable(pk, pv, True)
            for nk, nv in num_particles.items():
                self.add_experiment_variable(nk, nv, True)
        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv, True)
            for nk, nv in num_particles.items():
                self.add_experiment_variable(nk, nv, True)
        elif self.spec.satisfies("+weak"):
            scaled_variables = self.generate_weak_scaling_params(
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                {tuple(num_particles.keys()): list(num_particles.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)

        self.add_experiment_variable(
            "use_gpu",
            (
                "TRUE"
                if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm")
                else "FALSE"
            ),
        )

        self.add_experiment_variable("n_ranks", "{n_nodes}*{sys_cores_per_node}", True)

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        if self.spec.satisfies("+cuda"):
            system_specs["cuda_version"] = "{default_cuda_version}"
            system_specs["cuda_arch"] = "{cuda_arch}"
        if self.spec.satisfies("+rocm"):
            system_specs["rocm_arch"] = "{rocm_arch}"

        # set package spack specs
        self.add_spack_spec(system_specs["mpi"])

        self.add_spack_spec(
            self.name,
            [
                f"branson@{app_version} +metis n_groups={self.spec.variants['n_groups'][0]} ",
                system_specs["compiler"],
            ],
        )
