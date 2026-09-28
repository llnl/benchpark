# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.error import BenchparkError
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
from benchpark.scaling import Scaling, ScalingMode


class OsuMicroBenchmarks(
    Experiment,
    ProgrammingModel(
        ProgrammingModelType.Mpionly,
        ProgrammingModelType.Cuda,
        ProgrammingModelType.Rocm,
    ),
    Scaling(ScalingMode.Strong, ScalingMode.Throughput),
):

    two_rank_workloads = [
        "osu_bibw",
        "osu_bw",
        "osu_latency",
        "osu_get_acc_latency",
        "osu_get_bw",
        "osu_get_latency",
        "osu_put_bibw",
        "osu_put_bw",
        "osu_put_latency",
    ]

    scalable_workloads = [
        "osu_latency_mp",
        "osu_latency_mt",
        "osu_mbw_mr",
        "osu_multi_lat",
        "osu_allgather",
        "osu_allreduce_persistent",
        "osu_alltoallw",
        "osu_bcast_persistent",
        "osu_iallgather",
        "osu_ialltoallw",
        "osu_ineighbor_allgather",
        "osu_ireduce",
        "osu_neighbor_allgatherv",
        "osu_reduce_persistent",
        "osu_scatterv",
        "osu_allgather_persistent",
        "osu_alltoall",
        "osu_alltoallw_persistent",
        "osu_gather",
        "osu_iallgatherv",
        "osu_ibarrier",
        "osu_ineighbor_allgatherv",
        "osu_ireduce_scatter",
        "osu_neighbor_alltoall",
        "osu_reduce_scatter",
        "osu_scatterv_persistent",
        "osu_allgatherv",
        "osu_alltoall_persistent",
        "osu_barrier",
        "osu_gather_persistent",
        "osu_iallreduce",
        "osu_ibcast",
        "osu_ineighbor_alltoall",
        "osu_iscatter",
        "osu_neighbor_alltoallv",
        "osu_reduce_scatter_persistent",
        "osu_allgatherv_persistent",
        "osu_alltoallv",
        "osu_barrier_persistent",
        "osu_gatherv",
        "osu_ialltoall",
        "osu_igather",
        "osu_ineighbor_alltoallv",
        "osu_iscatterv",
        "osu_neighbor_alltoallw",
        "osu_scatter",
        "osu_allreduce",
        "osu_alltoallv_persistent",
        "osu_bcast",
        "osu_gatherv_persistent",
        "osu_ialltoallv",
        "osu_igatherv",
        "osu_ineighbor_alltoallw",
        "osu_neighbor_allgather",
        "osu_reduce",
        "osu_scatter_persistent",
        "osu_cas_latency",
        "osu_fop_latency",
        "osu_hello",
        "osu_init",
    ]

    variant(
        "workload",
        default="osu_latency",
        values=two_rank_workloads + scalable_workloads,
        multi=True,
        description="workloads available",
    )

    variant(
        "version",
        default="7.5",
        values=("latest", "7.5"),
        description="app version",
    )

    maintainers("nhanford")

    def compute_applications_section(self):

        if self.spec.satisfies("exec_mode=test"):
            num_nodes = {"n_nodes": 1, "n_ranks": 2}
            for pk, pv in num_nodes.items():
                self.add_experiment_variable(pk, pv, True)

        if self.spec.satisfies("+rocm"):
            self.add_experiment_variable("additional_args", " -d rocm", False)
        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("additional_args", " -d cuda", False)

        use_gpus = self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm")
        resource_var = "n_gpus" if use_gpus else "n_ranks"
        # self.add_experiment_variable("n_nodes", 2 , True)
        if any(self.spec.satisfies(f"workload={wl}") for wl in self.two_rank_workloads):
            if any(
                self.spec.satisfies(f"workload={wl}") for wl in self.scalable_workloads
            ):
                raise BenchparkError(
                    "This experiment must contain eithor only 2-rank workloads or only scalable workloads."
                )
            # Test the intra-node case and the inter-node case. Ignore user-set scaling params.
            self.add_experiment_variable(resource_var, [2, 2], True)
            self.add_experiment_variable("n_nodes", [1, 2], True)
            self.add_experiment_variable("scaling-iterations", 1, True)
        else:
            sys = self.system_spec.system
            # "Fill" the nodes with ranks, and scale according to user parameters.
            resources_per_node = (
                sys.sys_gpus_per_node if use_gpus else sys.sys_cores_per_node
            )
            self.add_experiment_variable(resource_var, resources_per_node, True)
            self.add_experiment_variable("n_nodes", 1, True)
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_nodes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    resource_var: lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "process_problem_size": "",
                    "total_problem_size": "",
                },
                ScalingMode.Throughput: {
                    "n_nodes": None,
                },
            }
        )

        n_resources = "{" + resource_var + "}"
        self.set_required_variables(
            n_resources=n_resources, process_problem_size="", total_problem_size=""
        )

    def compute_package_section(self):
        self.add_package_spec(
            self.name, [f"osu-micro-benchmarks{self.determine_version()}"]
        )
