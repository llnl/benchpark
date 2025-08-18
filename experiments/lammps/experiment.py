# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.scaling import StrongScaling
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment


class Lammps(
    Experiment,
    MpiOnlyExperiment,
    StrongScaling,
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
        default="20250204",
        description="app version",
    )

    variant(
        "gpu-aware-mpi",
        default=True,
        values=(True, False),
        when=("+cuda" or "+rocm"),
        description="Enable GPU-aware MPI",
    )

    maintainers("simongdg", "rfhaque")

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
            n_resources = {"n_nodes": 1, "n_ranks_per_node": 36}
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        elif self.spec.satisfies("+rocm"):
            n_resources = {"n_nodes": 8, "n_ranks_per_node": 8, "n_gpus": 64}
        elif self.spec.satisfies("+cuda"):
            n_resources = {"n_nodes": 4, "n_ranks_per_node": 4, "n_gpus": 16}
        else:
            n_resources = {"n_nodes": 1, "n_ranks_per_node": 36}
            self.add_experiment_variable("n_threads_per_proc", 1, True)

        if self.spec.satisfies("exec_mode=test"):
            for pk, pv in n_resources.items():
                self.add_experiment_variable(pk, pv, True)
        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(n_resources.keys()): list(n_resources.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv, True)

        self.add_experiment_variable("timesteps", 100, False)
        self.add_experiment_variable("input_file", "{input_path}/in.reaxff.hns", False)
        self.add_experiment_variable(
            "lammps_flags",
            f"{input_sizes} -k on {kokkos_mode} -sf kk -pk kokkos gpu/aware {kokkos_gpu_aware} neigh half comm {kokkos_comm} neigh/qeq full newton on -nocite",
            False,
        )

        self.set_required_variables(
            n_resources="{n_nodes}*{n_ranks_per_node}",
            process_problem_size="{xx}*{yy}*{zz}/{n_resources}",
            total_problem_size="{xx}*{yy}*{zz}",
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        fft_kokkos = (
            "fft_kokkos=cufft"
            if self.spec.satisfies("+cuda")
            else "fft_kokkos=hipfft" if self.spec.satisfies("+rocm") else ""
        )
        self.add_package_spec(
            self.name,
            [
                f"lammps@{app_version} +opt+manybody+molecule+kspace+rigid+kokkos+asphere+dpd-basic+dpd-meso+dpd-react+dpd-smooth+reaxff lammps_sizes=bigbig {fft_kokkos} "
            ],
        )
