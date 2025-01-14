# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment


class Genesis(Experiment, OpenMPExperiment):

    variant(
        "workload",
        default="DHFR",
        values=("DHFR", "ApoA1", "UUN", "cryoEM"),
        description="genesis",
    )

    variant(
        "version",
        default="main",
        description="app version",
    )

    def compute_applications_section(self):

        self.add_experiment_variable("experiment_setup", "")
        self.add_experiment_variable("lx", "32")
        self.add_experiment_variable("ly", "6")
        self.add_experiment_variable("lz", "4")
        self.add_experiment_variable("lt", "3")
        self.add_experiment_variable("px", "1")
        self.add_experiment_variable("py", "1")
        self.add_experiment_variable("pz", "1")
        self.add_experiment_variable("pt", "1")
        self.add_experiment_variable("tol_outer", "-1")
        self.add_experiment_variable("tol_inner", "-1")
        self.add_experiment_variable("maxiter_plus1_outer", "6")
        self.add_experiment_variable("maxiter_inner", "50")

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_nodes", ["2"], True)
            self.add_experiment_variable("processes_per_node", ["4"])
            self.add_experiment_variable("n_ranks", "{processes_per_node} * {n_nodes}")
            self.add_experiment_variable("omp_num_threads", ["12"])
            self.add_experiment_variable("arch", "OpenMP")

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        system_specs["lapack"] = "lapack"

        # if package_spec left empty spack will use external
        self.add_spack_spec(system_specs["mpi"])
        self.add_spack_spec(system_specs["lapack"])

        self.add_spack_spec(
            self.name, [f"genesis@{app_version} +mpi", system_specs["compiler"]]
        )
        self.add_spack_spec(
            system_specs["lapack"], [system_specs["lapack"], system_specs["compiler"]]
        )
