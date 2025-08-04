# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.caliper import Caliper

# from benchpark.affinity import Affinity


class MpiPingpong(Experiment, Caliper):

    variant(
        "workload",
        default="run",
    )

    maintainers("stephanielam3211")

    def compute_applications_section(self):
        n_nodes = 16  # max number of nodes
        expr_vars = {
            "n_nodes": n_nodes,
            # "iterations": [10]*5+[10000]*5+[100000]*5,
            # "msg_size": [16,256,4096,65536,1048576]*3
            # TODO: other expr vars?
            "iterations": 1000000,  # 1000000,
            "msg_size": 16384,  # [16,256,4096,65536,1048576]*1
        }

        for pk, pv in expr_vars.items():
            self.add_experiment_variable(pk, pv, True)

        self.add_experiment_variable("n_ranks", "{n_nodes}*{sys_cores_per_node}", True)

        self.add_experiment_variable("partner_rank", "{n_ranks}-1", True)

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{msg_size}",
            total_problem_size="{msg_size}",
        )

        # self.set_environment_variable(

        # )

    def compute_package_section(self):
        self.add_package_spec(self.name, ["mpi-pingpong@develop"])
