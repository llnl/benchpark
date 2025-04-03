# Copyright 2024 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.rocm import ROCmExperiment


class Scaffold(Experiment, ROCmExperiment):

    maintainers("michaelmckinsey1")

    variant(
        "workload",
        default="sweep",
        values=("sweep",),
    )

    variant(
        "scaffold_path",
        default=" ",
    )  # Path to cloned repo, since it is private.

    variant("version", default="develop", description="app version")

    def compute_applications_section(self):
        self.add_experiment_variable("n_gpus", 1, True)
        self.add_experiment_variable("n_ranks", 1, True)
        self.add_experiment_variable(
            "package_path", self.spec.variants["scaffold_path"][0], False
        )
        self.add_experiment_variable("timeout", 720, True)

    def compute_package_section(self):
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"scaffold@{app_version}"])
