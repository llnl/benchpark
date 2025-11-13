# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import math

from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import Scaling, ScalingMode


class RajaPerf(
    Experiment,
    MpiOnlyExperiment,
    CudaExperiment,
    ROCmExperiment,
    OpenMPExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
    Caliper,
):
    variant(
        "workload",
        default="suite",
        description="base Rajaperf suite or other problem",
    )

    variant(
        "version",
        default="2025.03.0",
        values=("develop", "latest", "2025.03.0"),
        description="app version",
    )

    variant(
        "exec_mode",
        default="test",
        values=("test", "perf", "singlenode_cpu_bandwidth"),
        description="Execution mode",
    )

    maintainers("michaelmckinsey1")

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            self.add_experiment_variable("process_problem_size", 1048576, True)
            self.add_experiment_variable("n_resources", 1, False)
        elif self.spec.satisfies("exec_mode=singlenode_cpu_bandwidth"):
            # Need large enough problem size to stress cache, so system dependent.
            # Examples dane: 128*1024**2, lassen: 64*1024**2, tuolumne: 256*1024**2, rzgenie: 32*1024*1024, poodle: 128*1024*1024
            sys = self.system_spec.system
            sockets = sys.sys_sockets_per_node
            L3size_bytes = sys.sys_cpu_L3_MB * 10**6
            L2size_bytes = sys.sys_cpu_L2_KB * 10**3
            num_cores = sys.sys_cores_per_node / sockets
            div_constant = 16  # 2 doubles per problem size
            cache_constant = 4  # Make sure data stays in cache
            if hasattr(sys, "sys_ccd_per_node"):
                L3size_bytes *= sys.sys_ccd_per_node / sockets
            problem_size = (
                (sockets * (L3size_bytes + L2size_bytes * num_cores))
                * cache_constant
                / div_constant
            )
            nearest_power_of_two = 2 ** round(math.log2(problem_size))
            self.add_experiment_variable(
                "process_problem_size", nearest_power_of_two, True
            )
            # Number of processes
            self.add_experiment_variable("n_resources", 1, False)

        self.set_required_variables(
            total_problem_size="{n_resources}*{process_problem_size}",
        )

        # In this application (RAJAPerf), since the input problem sizes (process_problem_size)
        # are per process sizes, strong scaling the problem implies that
        # as n_resources are scaled up, i.e. (x * scaling_factor),
        # process_problem_size are commensurately scaled down i.e. (x // scaling_factor)

        # For weak scaling, only the n_resources have to be scaled up,
        # process_problem_size remain the same
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_resources": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "process_problem_size": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    // scaling_factor,
                },
                ScalingMode.Weak: {
                    "n_resources": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "process_problem_size": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    ),
                },
                ScalingMode.Throughput: {
                    "n_resources": lambda var, itr, dim, scaling_factor: var.val(dim),
                    "process_problem_size": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                },
            }
        )

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        elif self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_ranks", "{n_resources}", True)
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"raja-perf{self.determine_version()} +mpi"])
