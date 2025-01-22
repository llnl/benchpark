# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.expr.builtin.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.openmp import OpenMPExperiment


class Babelstream(
    Experiment,
    Caliper,
    CudaExperiment,
    ROCmExperiment,
    OpenMPExperiment,
):
    variant(
        "workload",
        default="babelstream",
        description="babelstream",
    )

    variant(
        "version",
        default="caliper",
        values=("4.0", "develop", "caliper"),
        description="app version",
    )

    def compute_applications_section(self):

        self.add_experiment_variable("processes_per_node", "1", True)
        self.add_experiment_variable("n", "35", False)
        self.add_experiment_variable("o", "0", False)
        n_resources = 1

        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("execute", "cuda-stream", False)

        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("execute", "hip-stream", False)

        else:
            self.add_experiment_variable("n_ranks", n_resources, True)
            self.add_experiment_variable("execute", "omp-stream", False)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", n_resources, True)

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        if self.spec.satisfies("+cuda"):
            system_specs["cuda_version"] = "{default_cuda_version}"
            system_specs["cuda_arch"] = "{cuda_arch}"
        if self.spec.satisfies("+rocm"):
            system_specs["rocm_arch"] = "{rocm_arch}"

        # set package spack specs
        self.add_spack_spec(system_specs["mpi"])
        self.add_spack_spec(
            self.name, [f"babelstream@{app_version}", system_specs["compiler"]]
        )
