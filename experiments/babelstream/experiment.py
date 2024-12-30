# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.expr.builtin.caliper import Caliper
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment

class Babelstream(
    Experiment,
    Caliper,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
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

        array_size = {"s": 650000000}

        self.add_experiment_variable("processes_per_node", "1", True)
        self.add_experiment_variable("n", "35", False)
        self.add_experiment_variable("o", "0", False)
        n_resources = 1


        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_ranks", n_resources, True)
            self.add_experiment_variable("execute", "omp-stream", False)
            #self.add_experiment_variable("n_threads_per_proc", 1, True)
            #self.matrix_experiment_variables("n_threads_per_proc")
        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("execute", "cuda-stream", False)

        if self.spec.satisfies("+rocm"):
            self.add_experiment_variable("execute", "hip-stream", False)

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
