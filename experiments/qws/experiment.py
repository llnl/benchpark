# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment


class Qws(Experiment,
          OpenMPExperiment):
    variant(
        "workload",
        default="qws",
        description="qws",
    )

    def compute_applications_section(self):
        # env_vars = {}
        variables = {}

        variables["experiment_setup"] = ""
        variables["lx"] = "32"
        variables["ly"] = "6"
        variables["lz"] = "4"
        variables["lt"] = "3"
        variables["px"] = "1"
        variables["py"] = "1"
        variables["pz"] = "1"
        variables["pt"] = "1"
        variables["tol_outer"] = "-1"
        variables["tol_inner"] = "-1"
        variables["maxiter_plus1_outer"] = "6"
        variables["maxiter_inner"] = "50"

        if self.spec.satisfies("+openmp"):
            # env_vars["OMP_NUM_THREADS"] = "{omp_num_threads}"
            variables["processes_per_node"] = ["1"]
            variables["n_nodes"] = ["1"]
            variables["n_ranks"] = "{processes_per_node} * {n_nodes}"
            variables["omp_num_threads"] = ["48"]
            variables["arch"] = "OpenMP"

        # return {
        #     "qws": {
        #         "workloads": {
        #             "qws": {
        #                 # "env_vars": env_vars,
        #                 "experiments": {
        #                     "qws_mpi_{n_nodes}_{omp_num_threads}_{lx}_{ly}_{lz}_{lt}_{px}_{py}_{pz}_{pt}_{tol_outer}_{tol_inner}_{maxiter_plus1_outer}_{maxiter_inner}": {
        #                     "qws_omp_{n_nodes}_{omp_num_threads}_{lx}_{ly}_{lz}_{lt}_{px}_{py}_{pz}_{pt}_{tol_outer}_{tol_inner}_{maxiter_plus1_outer}_{maxiter_inner}": {
        #                         "variants": {
        #                             "package_manager": "spack",
        #                         },
        #                         "variables": variables,
        #                         },
        #                     },
        #                 },
        #             },
        #         },
        #     }
        # }

    def compute_spack_section(self):
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"

        self.add_spack_spec(
            self.name, [f"qws@master +mpi", system_specs["compiler"]]
        )
