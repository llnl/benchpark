# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import Scaling, ScalingMode


class Branson(
    Experiment,
    MpiOnlyExperiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak),
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

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            self.add_experiment_variable("num_particles", 1000000, True)
        else:
            self.add_experiment_variable("num_particles", 850000000, True)
        self.add_experiment_variable("resource_count", 1, False)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "resource_count": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
                ScalingMode.Weak: {
                    "resource_count": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "num_particles": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
            }
        )

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{resource_count}",
            process_problem_size="{num_particles}",
            total_problem_size="{num_particles} * {resource_count}",
        )

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("use_gpu", "TRUE")
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("use_gpu", "FALSE")
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(
            self.name,
            [
                f"branson@{app_version} n_groups={self.spec.variants['n_groups'][0]} ",
            ],
        )
