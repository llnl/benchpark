# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment


class Lammps(
    Experiment,
    OpenMPExperiment,
    CudaExperiment,
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

    variant(
        "gpu-aware-mpi",
        default=True,
        values=(True, False),
        when=("+cuda" or "+rocm"),
        description="Enable GPU-aware MPI",
    )

    url = "https://www.lammps.org/"

    def compute_applications_section(self):
        if self.spec.satisfies("+openmp"):
            problem_sizes = {"x": 8, "y": 8, "z": 8}
            kokkos_mode = "t {n_threads_per_proc}"
            kokkos_gpu_aware = "off"
            kokkos_comm = "host"
        elif self.spec.satisfies("+rocm") or self.spec.satisfies("+cuda"):
            problem_sizes = {"x": 20, "y": 40, "z": 32}
            kokkos_mode = "g 1"
            kokkos_gpu_aware = "on" if self.spec.satisfies("+rocm") else "off"
            kokkos_comm = "device"
        elif self.spec.satisfies("+cuda"):
            problem_sizes = {"x": 20, "y": 20, "z": 16}
            kokkos_mode = "g 1"
            kokkos_gpu_aware = "on" if self.spec.satisfies("+cuda") else "off"
            kokkos_comm = "device"
        else:
            problem_sizes = {"x": 8, "y": 8, "z": 8}
            kokkos_mode = "t {n_threads_per_proc}"
            kokkos_gpu_aware = "off"
            kokkos_comm = "host"

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
        elif self.spec.satisfies("+cuda"):
            self.add_experiment_variable("n_nodes", 4, True)
            self.add_experiment_variable("n_ranks_per_node", 4, True)
            self.add_experiment_variable("n_gpus", 16, True)
        else:
            self.add_experiment_variable("n_nodes", 1, True)
            self.add_experiment_variable("n_ranks_per_node", 36, True)
            self.add_experiment_variable("n_threads_per_proc", 1, True)

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
        system_specs["blas"] = "blas"

        # set package spack specs
        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["mpi"])

        if self.spec.satisfies("+cuda"):
            system_specs["cuda_version"] = "{default_cuda_version}"
            system_specs["cuda_arch"] = "{cuda_arch}"
        elif self.spec.satisfies("+rocm"):
            system_specs["rocm_arch"] = "{rocm_arch}"

        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["blas"])

        self.add_spack_spec(
            self.name,
            [
                f"lammps@{app_version} +mpi+opt+manybody+molecule+kspace+rigid+kokkos+asphere+dpd-basic+dpd-meso+dpd-react+dpd-smooth+reaxff lammps_sizes=bigbig ",
                system_specs["compiler"],
            ],
        )
