# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
from benchpark.scaling import Scaling, ScalingMode


class Branson(
    Experiment,
    ProgrammingModel(
        ProgrammingModelType.Mpionly,
        ProgrammingModelType.Openmp,
        ProgrammingModelType.Cuda,
        ProgrammingModelType.Rocm,
    ),
    Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
    Caliper,
):
    variant(
        "workload",
        default="branson",
        description="workload name",
    )

    variant(
        "version",
        default="develop",
        values=("develop",),
        description="app version",
    )

    variant(
        "n_groups",
        default="30",
        values=int,
        description="Number of groups",
    )

    variant(
        "decomposition",
        default="PARTICLE_PASS",
        values=("PARTICLE_PASS", "REPLICATED"),
        description="Domain decomposition type",
    )

    variant(
        "layout",
        default="SOA",
        values=("SOA", "AOS"),
        description="Particle storage layout",
    )

    variant(
        "algorithm",
        default="EVENT",
        values=("EVENT", "HISTORY"),
        description="Particle transport algorithm",
    )

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            self.add_experiment_variable("num_particles", 1000000, True)
            pool_size = 4
        else:
            if self.spec.satisfies("+throughput"):
                photons = [
                    10000000,
                    20000000,
                    40000000,
                    80000000,
                    100000000,
                    160000000,
                    200000000,
                    320000000,
                    400000000,
                    640000000,
                    800000000,
                    1000000000,
                    1280000000,
                    2000000000,
                    2560000000,
                    4000000000,
                    5120000000,
                ]
                pool_size = 64
            else:
                # photons = 100000000
                # pool_size = 20
                photons = 200000000
                pool_size = 32
            self.add_experiment_variable("num_particles", photons, True)
        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_nodes", 1, False)
            resource_count = "n_nodes"
            self.add_experiment_variable("resource_count", "{sys_cores_per_node} * {n_nodes}", False)
        else:
            self.add_experiment_variable("resource_count", 4, False)
            resource_count = "resource_count"
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("pool", pool_size, False)
        self.add_experiment_variable("input_file", "3D_hohlraum_single_node.xml", False)
        self.add_experiment_variable("particle_message_size", "640000", False)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    resource_count: lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
                ScalingMode.Weak: {
                    resource_count: lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "num_particles": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
                ScalingMode.Throughput: {
                    resource_count: None,
                    "num_particles": None,
                },
            }
        )

        self.add_experiment_variable(
            "decomposition", self.spec.variants["decomposition"][0], True
        )
        self.add_experiment_variable("layout", self.spec.variants["layout"][0], True)
        self.add_experiment_variable(
            "algorithm", self.spec.variants["algorithm"][0], True
        )

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{resource_count}",
            process_problem_size="{num_particles} / {resource_count}",
            total_problem_size="{num_particles}",
        )

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)
            self.set_environment_variable("FI_CXI_RX_MATCH_MODE", "hybrid")
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("use_gpu", "TRUE")
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("use_gpu", "FALSE")
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            umpire = "+umpire"
        else:
            umpire = "~umpire"
        self.add_package_spec(
            self.name,
            [
                f"branson@{app_version}{umpire} n_groups={self.spec.variants['n_groups'][0]} ",
            ],
        )
