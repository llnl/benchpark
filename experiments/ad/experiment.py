# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment


class Ad(Experiment):
    variant(
        "workload",
        default="ad",
        description="ad",
    )

    variant(
        "version",
        default="main",
        description="app version",
    )

    maintainers("rfhaque")

    def compute_applications_section(self):
        self.add_experiment_variable("n_ranks", 1, True)
        self.add_experiment_variable("n_threads_per_proc", 1, True)

        self.set_required_variables(
            n_resources="{n_ranks}", process_problem_size="", total_problem_size=""
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"ad@{app_version}"])
