# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment


class Quicksilver(Experiment, OpenMPExperiment):
    variant(
        "workload",
        default="quicksilver",
        description="quicksilver",
    )

    variant(
        "experiment",
        default="weak",
        values=("weak", "strong"),
        description="weak or strong scaling",
    )

    variant(
        "version",
        default="master",
        description="app version",
    )

    def compute_applications_section(self):
        self.add_experiment_variable("n_threads_per_proc", "1")
        self.add_experiment_variable("n_ranks", "{I}*{J}*{K}", True)
        self.add_experiment_variable("n", "{x}*{y}*{z}*10")
        self.add_experiment_variable("x", "{X}")
        self.add_experiment_variable("y", "{Y}")
        self.add_experiment_variable("z", "{Z}")
        if self.spec.satisfies("scaling=weak"):
            self.add_experiment_name_prefix("weak")
            self.add_experiment_variable("X", ["32", "32", "64", "64"])
            self.add_experiment_variable("Y", ["32", "32", "32", "64"])
            self.add_experiment_variable("Z", ["16", "32", "32", "32"])
        else:
            self.add_experiment_name_prefix("strong")
            self.add_experiment_variable("X", "32")
            self.add_experiment_variable("Y", "32")
            self.add_experiment_variable("Z", "16")
        self.add_experiment_variable("I", ["2", "2", "4", "4"])
        self.add_experiment_variable("J", ["2", "2", "2", "4"])
        self.add_experiment_variable("K", ["1", "2", "2", "2"])

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # TODO: express that we need certain variables from system
        # Does not need to happen before merge, separate task
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"

        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["mpi"])

        self.add_spack_spec(
            self.name, [f"quicksilver@{app_version} +mpi", system_specs["compiler"]]
        )
