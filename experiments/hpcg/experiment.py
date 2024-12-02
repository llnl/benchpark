# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.scaling import StrongScaling
from benchpark.expr.builtin.caliper import Caliper


class Hpcg(
    Experiment,
    OpenMPExperiment,
    Caliper,
):


    variant(
        "workload",
        default="standard",
        description="workload to run",
    )
    variant(
        "version",
        default="3.1",
        values=("3.1", "develop", "caliper"),
        description="app version",
    )

    def compute_applications_section(self):
        # TODO: Replace with conflicts clause
        scaling_modes = {
            "single_node": self.spec.satisfies("+single_node"),
        }

        scaling_mode_enabled = [key for key, value in scaling_modes.items() if value]
        if len(scaling_mode_enabled) != 1:
            print(scaling_mode_enabled)
            raise BenchparkError(
                f"Only one type of scaling per experiment is allowed for application package {self.name}"
            )

        if self.spec.satisfies("+single_node"):
            self.add_experiment_variable(
                "mx", '104', True
            )

            self.add_experiment_variable(
                "my", '104', True
            )
            
            self.add_experiment_variable(
                "mz", '104', True
            )

            self.add_experiment_variable(
                "matrix_size", '{mx} {my} {mz}', False
            )

            self.add_experiment_variable(
                "iterations", '60', False
            )

            self.add_experiment_variable(
                "n_threads_per_proc", ['8', '16'], True
            )
     
            self.add_experiment_variable(
                "n_ranks_per_node", '1', False
            )

            self.add_experiment_variable(
                "n_nodes", '1', False
            )

            #self.add_experiment_variable(
             #   "env_name", 'hpcg-omp', False
            #)

            self.matrix_experiment_variables('n_threads_per_proc')

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"

        # set package spack specs
        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["mpi"])
        # self.add_spack_spec(system_specs["blas"])

        self.add_spack_spec(
            self.name, [f"hpcg@{app_version}", system_specs["compiler"]]
        )
