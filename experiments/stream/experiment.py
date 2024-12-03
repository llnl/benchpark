# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.scaling import ThroughputScaling
from benchpark.expr.builtin.caliper import Caliper

class Stream(
    Experiment,
    ThroughputScaling,
    Caliper,
):
    variant(
        "workload",
        default="stream",
        description="stream",
    )

    variant(
        "version",
        default="5.10",
        description="app version",
    )

    def compute_applications_section(self):
        # TODO: Replace with conflicts clause
        scaling_modes = {
            "throughput": self.spec.satisfies("+throughput"),
            "single_node": self.spec.satisfies("+single_node"),
        }

        scaling_mode_enabled = [key for key, value in scaling_modes.items() if value]
        if len(scaling_mode_enabled) != 1:
            raise BenchparkError(
                f"Only one type of scaling per experiment is allowed for application package {self.name}"
            )

        array_size = {"s": 32000000}

        self.add_experiment_variable("processes_per_node", "1", True)
        self.add_experiment_variable("n", "35", True)
        self.add_experiment_variable("o", "0", True)
        self.add_experiment_variable("n_ranks", "{sys_cores_per_node}", True)

        if self.spec.satisfies("+single_node"):
            for pk, pv in array_size.items():
                self.add_experiment_variable(pk, pv, True)

        elif self.spec.satisfies("+throughput"):
            scaled_variables = self.generate_throughput_scaling_params(
                {tuple(array_size.keys()): list(array_size.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)

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

        self.add_spack_spec(
            self.name, [f"stream@{app_version}", system_specs["compiler"]]
        )
