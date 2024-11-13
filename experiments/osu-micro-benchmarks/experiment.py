from benchpark.directives import variant
from benchpark.error import BenchparkError
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
import re


class OsuMicroBenchmarks(Experiment):

    variant(
        "version",
        default="develop",
        description="app version",
    )

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
	scaling_modes = {
            "strong": self.spec.satisfies("strong=oui"),
            "single_node": self.spec.satisfies("single_node=oui"),
        }

        scaling_mode_enabled = [key for key, value in scaling_modes.items() if value]
        if len(scaling_mode_enabled) != 1:
            raise BenchparkError(
                f"Only one type of scaling per experiment is allowed for application package {self.name}"
            )

        variables = {}
	num_nodes = {"n_nodes", 1}
        variables["scaling_nodes"] = "2"
        variables["n_nodes"] = "{scaling_nodes}"
        variables["n_ranks_per_node"] = "36"

        pattern = r"workload=(?P<workload>[^ ]+)\s*"
        workload = re.search(pattern, str(self.spec.variants))
        workload_string = workload.group(1)

	if self.spec.satisfies("single_node=oui"):
            for pk, pv in num_nodes.items():
                self.add_experiment_variable(pk, pv, True)

	elif self.spec.satisfies("strong=oui"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv, True)
       # return {
        #    "osu-micro-benchmarks": {
         #       # TODO replace with a hash once we have one?
          #      "workloads": {
           #         workload_string: {
            #            "experiments": {
             #               "scaling_{n_nodes}nodes_medium": {
	#		        "variants": {
         #                           "package_manager": "spack",
          #                      },
           #                     "variables": variables,
            #                }
             #           }
              #      }
               # }
           # }
        }

    def compute_spack_section(self):
	app_version = self.spec.variants["version"][0]
        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        # set package spack specs
        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["mpi"])
        self.add_spack_spec(
            self.name, [f"osu-micro-benchmarks@{app_version}", system_specs["compiler"]]
        )
        # TODO: express that we need certain variables from system
        # Does not need to happen before merge, separate task
        #osu_microbenchmarks_spack_spec = "osu-micro-benchmarks"
       # packages = ["default-mpi", self.spec.name]

#        return {
 #           "packages": {
  #              "osu-micro-benchmarks": {
   #                 "pkg_spec": osu_microbenchmarks_spack_spec,
    #                "compiler": "default-compiler",
     #           }
      #      },
       #     "environments": {"osu-micro-benchmarks": {"packages": packages}},
            
       # }
