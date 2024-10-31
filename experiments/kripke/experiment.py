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
from benchpark.scaling import ThroughputScaling


class Kripke(
    Experiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    StrongScaling,
    WeakScaling,
    ThroughputScaling,
):
    variant(
        "workload",
        default="kripke",
        description="problem1 or problem2",
    )

    variant(
        "version",
        default="develop",
        description="app version",
    )

    def compute_applications_section(self):
        # TODO: Replace with conflicts clause
        scaling_modes = {
            "strong": self.spec.satisfies("strong=oui"),
            "weak": self.spec.satisfies("weak=oui"),
            "throughput": self.spec.satisfies("throughput=oui"),
            "single_node": self.spec.satisfies("single_node=oui"),
        }

        scaling_mode_enabled = [key for key, value in scaling_modes.items() if value]
        if len(scaling_mode_enabled) != 1:
            raise BenchparkError(
                f"Only one type of scaling per experiment is allowed for application package {self.name}"
            )

        input_variables = {
            "ngroups": 64,
            "gs": 1,
            "nquad": 128,
            "ds": 128,
            "lorder": 4,
        }

        # Number of processes in each dimension
        num_procs = {"npx": 2, "npy": 2, "npz": 1}

        # Number of zones in each dimension, per process
        problem_sizes = {"nzx": 64, "nzy": 64, "nzz": 32}

        for k, v in input_variables.items():
            self.add_experiment_variable(k, v, True)

        if self.spec.satisfies("single_node=oui"):
            n_resources = 1
            # TODO: Check if n_ranks / n_resources_per_node <= 1
            for pk, pv in num_procs.items():
                self.add_experiment_variable(pk, pv, True)
                n_resources *= pv
            for nk, nv in problem_sizes.items():
                self.add_experiment_variable(nk, nv, True)
        elif self.spec.satisfies("throughput=oui"):
            n_resources = 1
            for pk, pv in num_procs.items():
                self.add_experiment_variable(pk, pv, True)
                n_resources *= pv
            scaled_variables = self.generate_throughput_scaling_params(
                {tuple(problem_sizes.keys()): list(problem_sizes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for nk, nv in scaled_variables.items():
                self.add_experiment_variable(nk, nv, True)
        elif self.spec.satisfies("strong=oui"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(num_procs.keys()): list(num_procs.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv, True)
            n_resources = [
                x * y * z
                for x, y, z in zip(
                    *(scaled_variables[p] for p in num_procs if p in scaled_variables)
                )
            ]
            for nk, nv in problem_sizes.items():
                self.add_experiment_variable(nk, nv, True)
        elif self.spec.satisfies("weak=oui"):
            scaled_variables = self.generate_weak_scaling_params(
                {tuple(num_procs.keys()): list(num_procs.values())},
                {tuple(problem_sizes.keys()): list(problem_sizes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            n_resources = [
                x * y * z
                for x, y, z in zip(
                    *(scaled_variables[p] for p in num_procs if p in scaled_variables)
                )
            ]
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)

        if self.spec.satisfies("openmp=oui"):
            self.add_experiment_variable("n_ranks", n_resources, True)
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        elif self.spec.satisfies("cuda=oui") or self.spec.satisfies("rocm=oui"):
            self.add_experiment_variable("n_gpus", n_resources, True)

        if self.spec.satisfies("openmp=oui"):
            self.add_experiment_variable("arch", "OpenMP")
        elif self.spec.satisfies("cuda=oui"):
            self.add_experiment_variable("arch", "CUDA")
        elif self.spec.satisfies("rocm=oui"):
            self.add_experiment_variable("arch", "HIP")

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        if self.spec.satisfies("cuda=oui"):
            system_specs["cuda_version"] = "{default_cuda_version}"
            system_specs["cuda_arch"] = "{cuda_arch}"
        if self.spec.satisfies("rocm=oui"):
            system_specs["rocm_arch"] = "{rocm_arch}"

        # set package spack specs
        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["mpi"])

        self.add_spack_spec(
            self.name, [f"kripke@{app_version} +mpi", system_specs["compiler"]]
        )
