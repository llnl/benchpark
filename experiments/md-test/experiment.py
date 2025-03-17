# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling


class MdTest(
    Experiment,
    StrongScaling,
):
    variant(
        "workload",
        default="multi-file",
        description="base md-test or other problem",
    )

    variant(
        "version",
        default="1.9.3",
        description="app version",
    )

    def compute_applications_section(self):

        num_resources = {"n_ranks": 1}

        self.add_experiment_variable("num-objects", "1000", True)
        self.add_experiment_variable("iterations", "10", True)

        if self.spec.satisfies("+single_node"):
            for pk, pv in num_resources.items():
                self.add_experiment_variable(pk, pv, True)
        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(num_resources.keys()): list(num_resources.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"

        # set package spack specs
        self.add_package_spec(system_specs["mpi"])

        self.add_package_spec("ior", ["ior@3.3.0", system_specs["compiler"]])
        self.add_package_spec(
            self.name, [f"mdtest@{app_version}", system_specs["compiler"]]
        )
