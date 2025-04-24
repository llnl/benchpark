# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.caliper import Caliper
from benchpark.affinity import Affinity


class MpiPingpong(Experiment, Caliper, Affinity):

    variant(
        "workload",
        default="run",
    )

    maintainers("stephanielam3211")

    def compute_applications_section(self):

        expr_vars = {
            "n_ranks": [112]*5, #[113]*5,
            #"n_nodes" : 2,
            #"iterations": [10]*5+[10000]*5+[100000]*5,
            #"msg_size": [16,256,4096,65536,1048576]*3
            # TODO: other expr vars?
            "iterations" : [1000000]*5, #[1000000]*5,
            "msg_size" : [16000, 32000, 64000, 128000, 256000]*1      #[16,256,4096,65536,1048576]*1
        }

        for pk, pv in expr_vars.items():
            self.add_experiment_variable(pk, pv, True)

    def compute_package_section(self):
        self.add_package_spec(self.name, ["mpi-pingpong@main"])
