# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.caliper import Caliper


class MpiPingpong(Experiment, Caliper):

    variant(
        "workload",
        default="run",
    )

    maintainers("stephanielam3211")

    def compute_applications_section(self):

        expr_vars = {
            "n_ranks": 2,
            "iterations": 10
            # TODO: other expr vars?
        }

        for pk, pv in expr_vars.items():
            self.add_experiment_variable(pk, pv, True)

    def compute_package_section(self):
        self.add_package_spec(self.name, ["mpi-pingpong@main"])
