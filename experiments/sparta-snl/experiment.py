# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.cuda import CudaExperiment
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.rocm import ROCmExperiment


class SpartaSnl(
    Experiment,
    MpiOnlyExperiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
):
    variant(
        "workload",
        default="cylinder",
        values=("cylinder",),
        description="workloads",
    )

    variant(
        "version",
        default="master",
        values=("master",),
        description="app version",
    )

    variant(
        "fft",
        default="fftw3",
        description="Which FFT library to use",
        values=("fftw3", "mkl", "kiss"),
        multi=False,
    )

    variant(
        "fft_kokkos",
        default="fftw3",
        description="FFT library for Kokkos package",
        values=("kiss", "fftw3", "mkl", "hipfft", "cufft"),
        multi=False,
    )

    variant(
        "gpu-aware-mpi",
        default=True,
        values=(True, False),
        description="Enable GPU-aware MPI",
    )

    maintainers("rfhaque")

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            L = 1
            ppc = 16
            stats = 10
            run = 100
            xmin = -1.0
            xmax = 1.1
            ymin = -1.1
            ymax = 1.1
        else:
            L = 2  # will increase problem size by 4X
            ppc = 64
            stats = 10
            run = 100
            xmin = -1.0
            xmax = 1.1
            ymin = -1.1
            ymax = 1.1

        if self.spec.satisfies("workload=cylinder"):
            self.add_experiment_variable("L", L, True)
            self.add_experiment_variable("ppc", ppc, True)
            self.add_experiment_variable("xmin", xmin, True)
            self.add_experiment_variable("xmax", xmax, True)
            self.add_experiment_variable("ymin", ymin, True)
            self.add_experiment_variable("ymax", ymax, True)

        self.add_experiment_variable("stats", stats, True)
        self.add_experiment_variable("run", run, True)

        if self.spec.satisfies("+rocm") or self.spec.satisfies("+cuda"):
            kokkos_mode = "g 1"
            kokkos_gpu_aware = "yes" if self.spec.satisfies("+gpu-aware-mpi") else "no"
        else:
            kokkos_mode = "t {n_threads_per_proc}"
            kokkos_gpu_aware = "no"

        self.add_experiment_variable(
            "sparta_flags",
            f"-k on {kokkos_mode} -sf kk -pk kokkos gpu/aware {kokkos_gpu_aware}",
            False,
        )

        self.add_experiment_variable("n_resources", 4, False)

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

        if self.spec.satisfies("workload=cylinder"):
            self.add_experiment_variable("in", "in.cylinder", False)

            self.set_required_variables(
                process_problem_size="{L}*{ppc}*1000",  # 1000 is a placeholder multiplier
                total_problem_size="{process_problem_size}*{n_resources}",
            )

    def compute_package_section(self):
        fft = self.spec.variants["fft"][0]
        fft_kokkos = self.spec.variants["fft_kokkos"][0]
        if self.spec.satisfies("+cuda"):
            fft_kokkos = "cufft"
        if self.spec.satisfies("+rocm"):
            fft_kokkos = "hipfft"

        self.add_package_spec(
            self.name,
            [
                f"sparta-snl{self.determine_version()} +mpi+kokkos fft_kokkos={fft_kokkos} fft={fft} "
            ],
        )
