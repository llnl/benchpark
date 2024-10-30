from benchpark.directives import variant
from benchpark.experiment import Experiment
import re


class OsuMicroBenchmarks(Experiment):
    variant(
        "workload",
        default="osu_latency",
        values=(
            "osu_bibw",
            "osu_bw",
            "osu_latency",
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
            "osu_acc_latency",
            "osu_cas_latency",
            "osu_fop_latency",
            "osu_get_acc_latency",
            "osu_get_bw",
            "osu_get_latency",
            "osu_put_bibw",
            "osu_put_bw",
            "osu_put_latency",
            "osu_hello",
            "osu_init",
        ),
        description="workloads available",
    )

    def compute_applications_section(self):
        variables = {}

        variables["scaling_nodes"] = "2"
        variables["n_nodes"] = "{scaling_nodes}"
        variables["n_ranks_per_node"] = "36"

        pattern = r"workload=(?P<workload>[^ ]+)\s*"
        workload = re.search(pattern, str(self.spec.variants))
        workload_string = workload.group(1)

        return {
            "osu-micro-benchmarks": {
                # TODO replace with a hash once we have one?
                "workloads": {
                    workload_string: {
                        "experiments": {
                            "scaling_{n_nodes}nodes_medium": {
			        "variants": {
                                    "package_manager": "spack",
                                },
                                "variables": variables,
                            }
                        }
                    }
                }
            }
        }

    def compute_spack_section(self):
        # TODO: express that we need certain variables from system
        # Does not need to happen before merge, separate task
        osu_microbenchmarks_spack_spec = "osu-micro-benchmarks"
        packages = ["default-mpi", self.spec.name]

        return {
            "packages": {
                "osu-micro-benchmarks": {
                    "pkg_spec": osu_microbenchmarks_spack_spec,
                    "compiler": "default-compiler",
                }
            },
            "environments": {"osu-micro-benchmarks": {"packages": packages}},
            
        }
