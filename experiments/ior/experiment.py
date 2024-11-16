# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
from benchpark.scaling import WeakScaling


class Ior(
    Experiment,
    StrongScaling,
    WeakScaling,
):
    variant(
        "workload",
        default="ior",
        description="base IOR  or other problem",
    )

    variant(
        "version",
        default="3.3.0",
        description="app version",
    )

    def compute_applications_section(self):
        # TODO: Replace with conflicts clause
        scaling_modes = {
            "strong": self.spec.satisfies("strong=oui"),
            "weak": self.spec.satisfies("weak=oui"),
            "single_node": self.spec.satisfies("single_node=oui"),
        }

        scaling_mode_enabled = [key for key, value in scaling_modes.items() if value]
        if len(scaling_mode_enabled) != 1:
            raise BenchparkError(
                f"Only one type of scaling per experiment is allowed for application package {self.name}"
            )

        num_nodes = {"n_nodes": 1}
        t = "{b}/256"
        self.add_experiment_variable("t", t, True)

        if self.spec.satisfies("single_node=oui"):
            for pk, pv in num_nodes.items():
                self.add_experiment_variable(pk, pv, True)
            self.add_experiment_variable("b", "268435456", True)
        elif self.spec.satisfies("strong=oui"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)
            # 256 mb
            self.add_experiment_variable("b", "268435456 / {n_nodes}", True)
        elif self.spec.satisfies("weak=oui"):
            scaled_variables = self.generate_weak_scaling_params(
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)

            self.add_experiment_variable("b", "268435456", True)

        self.add_experiment_variable("t", t, True)
        self.add_experiment_variable(
            "n_ranks", "{sys_cores_per_node} * {n_nodes}", True
        )

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"

        # set package spack specs
        self.add_spack_spec(system_specs["mpi"])

        self.add_spack_spec(self.name, [f"ior@{app_version}", system_specs["compiler"]])
