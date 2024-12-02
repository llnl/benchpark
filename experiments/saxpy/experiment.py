# Copyright 2024 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.expr.builtin.caliper import Caliper


class Saxpy(Experiment, OpenMPExperiment, CudaExperiment, ROCmExperiment, Caliper):
    variant(
        "workload",
        default="problem",
        description="problem",
    )

    variant(
        "version",
        default="1.0.0",
        description="app version",
    )

    def compute_applications_section(self):
        # GPU tests include some smaller sizes
        n = ["512", "1024"]
        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_nodes", ["1", "2"], True)
            self.add_experiment_variable("n_ranks", "8")
            self.add_experiment_variable("n_threads_per_proc", ["2", "4"], True)
            self.matrix_experiment_variables(["n", "n_threads_per_proc"])
        else:
            n = ["128", "256"] + n
            self.add_experiment_variable("n_gpus", "1", False)
            self.matrix_experiment_variables("n")

        self.add_experiment_variable("n", n, True)

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # TODO: express that we need certain variables from system
        # Does not need to happen before merge, separate task
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"

        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["mpi"])

        self.add_spack_spec(
            self.name, [f"saxpy@{app_version}", system_specs["compiler"]]
        )
