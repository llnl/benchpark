# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.scaling import StrongScaling
from benchpark.scaling import WeakScaling
from benchpark.caliper import Caliper


class Quicksilver(
    Experiment,
    OpenMPExperiment,
    StrongScaling,
    WeakScaling,
    Caliper,
):
    variant(
        "workload",
        default="quicksilver",
        description="quicksilver",
    )

    variant(
        "version",
        default="caliper",
        values=("master", "caliper"),
        description="app version",
    )

    maintainers("rfhaque")

    def compute_applications_section(self):
        self.add_experiment_variable("n_threads_per_proc", "1")
        self.add_experiment_variable("n_ranks", "{I}*{J}*{K}", True)
        self.add_experiment_variable("n", "{x}*{y}*{z}*10")
        self.add_experiment_variable("x", "{X}")
        self.add_experiment_variable("y", "{Y}")
        self.add_experiment_variable("z", "{Z}")
        if self.spec.satisfies("+weak"):
            self.add_experiment_variable("X", ["32", "32", "64", "64"])
            self.add_experiment_variable("Y", ["32", "32", "32", "64"])
            self.add_experiment_variable("Z", ["16", "32", "32", "32"])
        else:
            self.add_experiment_variable("X", "32")
            self.add_experiment_variable("Y", "32")
            self.add_experiment_variable("Z", "16")
        self.add_experiment_variable("I", ["2", "2", "4", "4"])
        self.add_experiment_variable("J", ["2", "2", "2", "4"])
        self.add_experiment_variable("K", ["1", "2", "2", "2"])

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{n}/{n_ranks}",
            total_problem_size="{n}",
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"quicksilver@{app_version} +mpi"])
