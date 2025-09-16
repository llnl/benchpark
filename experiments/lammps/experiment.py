# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import ScalingMode, Scaling


class Lammps(
    Experiment,
    MpiOnlyExperiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    Scaling(ScalingMode.Strong),
):
    variant(
        "workload",
        default="hns-reaxff",
        values=("hns-reaxff", "lj", "eam", "chain", "chute", "rhodo"),
        description="workloads",
    )

    variant(
        "version",
        default="20250722",
        values=("develop", "latest", "20250722", "stable_29Aug2024_update3"),
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
        if self.spec.satisfies("exec_mode=test"):
            total_problem_sizes = {"x": 8, "y": 8, "z": 8}
        else:
            total_problem_sizes = {"x": 20, "y": 40, "z": 32}

        self.add_experiment_variable(
            "total_problem_size_dict", total_problem_sizes, True
        )
        input_sizes = " ".join(f"-v {k} {{{k}}}" for k in total_problem_sizes.keys())

        if self.spec.satisfies("+rocm") or self.spec.satisfies("+cuda"):
            kokkos_mode = "g 1"
            kokkos_gpu_aware = "on" if self.spec.satisfies("+rocm") else "off"
            kokkos_comm = "device"
        else:
            kokkos_mode = "t {n_threads_per_proc}"
            kokkos_gpu_aware = "off"
            kokkos_comm = "host"

        self.add_experiment_variable(
            "lammps_flags",
            f"{input_sizes} -k on {kokkos_mode} -sf kk -pk kokkos gpu/aware {kokkos_gpu_aware} neigh half comm {kokkos_comm} neigh/qeq full newton on -nocite",
            False,
        )

        self.add_experiment_variable("n_resources", 1, False)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_resources": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "total_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    ),
                },
            }
        )

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

        self.add_experiment_variable("timesteps", 100, False)
        self.add_experiment_variable("input_file", "{input_path}/in.reaxff.hns", False)

        self.set_required_variables(
            process_problem_size="{x}*{y}*{z}/{n_resources}",
            total_problem_size="{x}*{y}*{z}",
        )

    def compute_package_section(self):
        fft_kokkos = (
            "fft_kokkos=cufft"
            if self.spec.satisfies("+cuda")
            else "fft_kokkos=hipfft" if self.spec.satisfies("+rocm") else ""
        )
        self.add_package_spec(
            self.name,
            [
                f"lammps{self.determine_version()} +opt+manybody+molecule+kspace+rigid+kokkos+asphere+dpd-basic+dpd-meso+dpd-react+dpd-smooth+reaxff lammps_sizes=bigbig {fft_kokkos} "
            ],
        )
