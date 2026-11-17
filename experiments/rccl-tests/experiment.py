# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType


class RcclTests(
    Experiment,
    ProgrammingModel(
        ProgrammingModelType.Rocm,
    ),
):
    two_rank_workloads = ("send-recv",)

    variant(
        "workload",
        default="all-reduce",
        values=(
            "all-gather",
            "all-reduce",
            "all-reduce-bias",
            "all-to-all",
            "all-to-allv",
            "broadcast",
            "gather",
            "hypercube",
            "reduce",
            "reduce-scatter",
            "scatter",
            "send-recv",
        ),
        multi=True,
        description="rccl-tests collectives to run",
    )

    variant(
        "version",
        default="develop",
        values=("latest", "develop", "master"),
        description="app version",
    )

    maintainers("nhanford")

    def compute_applications_section(self):
        # One MPI rank per GPU; RCCL does the communication between them.
        if self.spec.satisfies("exec_mode=test"):
            self.add_experiment_variable("n_nodes", 1, True)
            self.add_experiment_variable("end_message_size", "128M", False)
            self.add_experiment_variable("num_iters", 20, False)
        else:  # exec_mode=perf: cross the network
            self.add_experiment_variable("n_nodes", 2, True)
            self.add_experiment_variable("end_message_size", "8G", False)
            self.add_experiment_variable("num_iters", 100, False)

        if any(
            self.spec.satisfies(f"workload={workload}")
            for workload in self.two_rank_workloads
        ):
            self.add_experiment_variable("n_gpus", 2, True)
        else:
            self.add_experiment_variable(
                "n_gpus", "{n_nodes}*{sys_gpus_per_node}", True
            )
        self.add_experiment_variable("num_gpus_per_task", 1, False)

        # Each test sweeps message sizes, so there is no single problem size
        self.set_required_variables(
            n_resources="{n_gpus}", process_problem_size="", total_problem_size=""
        )

        if self.spec.satisfies("+rocm") and self.system_spec.name == "llnl-elcapitan":
            net_plugin = self.system_spec.system.system_specific_variables().get(
                "rccl_net_plugin"
            )
            if net_plugin:
                self.set_environment_variable("NCCL_NET_PLUGIN", net_plugin)

            # Match rccl/fast-env-slows-mpi on LLNL Slingshot systems.
            for name, value in {
                "FI_MR_CACHE_MONITOR": "userfaultfd",
                "NCCL_SOCKET_IFNAME": "hsi",
                "FI_CXI_RDZV_PROTO": "alt_read",
                "FI_CXI_RDZV_THRESHOLD": "0",
                "FI_CXI_RDZV_GET_MIN": "0",
                "FI_CXI_RDZV_EAGER_SIZE": "0",
                "FI_CXI_DEFAULT_TX_SIZE": "1024",
                "FI_CXI_DISABLE_HOST_REGISTER": "1",
                "FI_CXI_DEFAULT_CQ_SIZE": "131072",
                "FI_CXI_RX_MATCH_MODE": "hybrid",
            }.items():
                self.set_environment_variable(name, value)

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"rccl-tests{self.determine_version()} +mpi"])
