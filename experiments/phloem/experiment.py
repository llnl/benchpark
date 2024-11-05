# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling


class Phloem(Experiment, StrongScaling):
    variant(
        "workload",
        default="sqmr",
        values=("sqmr", "mpiBench", "mpiGraph"),
        description="sqmr, mpiBench, or mpiGraph",
    )

    variant(
        "version",
        default="master",
        description="app version",
    )

    def compute_applications_section(self):
        if self.spec.satisfies("workload=sqmr"):
            self.add_experiment_variable(
                "n_ranks", "{num_cores}*{num_nbors}+{num_cores}"
            )
            self.add_experiment_variable("num_cores", "4")
            self.add_experiment_variable("num_nbors", "{num_cores}")
        elif self.spec.satisfies("workload=mpiBench"):
            self.add_experiment_variable("n_ranks", "2")
        elif self.spec.satisfies("workload=mpiGraph"):
            self.add_experiment_variable("n_ranks", "2")

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"

        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["mpi"])

        self.add_spack_spec(
            self.name, [f"phloem@{app_version} +mpi", system_specs["compiler"]]
        )
