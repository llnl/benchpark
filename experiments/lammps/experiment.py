# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.rocm import ROCmExperiment


class Lammps(
    Experiment,
    OpenMPExperiment,
    ROCmExperiment,
):
    variant(
        "workload",
        default="hns-reaxff",
        values=("hns-reaxff", "lj", "eam", "chain", "chute", "rhodo"),
        description="workloads",
    )

    variant(
        "version",
        default="20231121",
        description="app version",
    )

    def compute_applications_section(self):
        if self.spec.satisfies("+openmp"):
            problem_sizes = {"x": 8, "y": 8, "z": 8}
            kokkos_mode = "t {n_threads_per_proc}"
            kokkos_gpu_aware = "off"
            kokkos_comm = "host"
        elif self.spec.satisfies("+rocm"):
            problem_sizes = {"x": 20, "y": 40, "z": 32}
            kokkos_mode = "g 1"
            kokkos_gpu_aware = "on"
            kokkos_comm = "device"

        for nk, nv in problem_sizes.items():
            self.add_experiment_variable(nk, nv, True)

        input_sizes = " ".join(f"-v {k} {{{k}}}" for k in problem_sizes.keys())

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_nodes", 1, True)
            self.add_experiment_variable("n_ranks_per_node", 36, True)
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_nodes", 8, True)
            self.add_experiment_variable("n_ranks_per_node", 8, True)
            self.add_experiment_variable("n_gpus", 64, True)

        self.add_experiment_variable("timesteps", 100, False)
        self.add_experiment_variable("input_file", "{input_path}/in.reaxc.hns", False)
        self.add_experiment_variable(
            "lammps_flags",
            f"{input_sizes} -k on {kokkos_mode} -sf kk -pk kokkos gpu/aware {kokkos_gpu_aware} neigh half comm {kokkos_comm} neigh/qeq full newton on -nocite",
            False,
        )

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        if self.spec.satisfies("+rocm"):
            system_specs["rocm_arch"] = "{rocm_arch}"
            system_specs["blas"] = "blas-rocm"

        # set package spack specs
        if self.spec.satisfies("+rocm"):
            # empty package_specs value implies external package
            self.add_spack_spec(system_specs["blas"])
        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["mpi"])

        self.add_spack_spec(
            self.name,
            [
                f"lammps@{app_version} +opt+manybody+molecule+kspace+rigid+kokkos+asphere+dpd-basic+dpd-meso+dpd-react+dpd-smooth+reaxff lammps_sizes=bigbig ",
                system_specs["compiler"],
            ],
        )
