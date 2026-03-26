# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
from benchpark.scaling import Scaling, ScalingMode


class Lammps(
    Experiment,
    ProgrammingModel(
        ProgrammingModelType.Mpionly,
        ProgrammingModelType.Openmp,
        ProgrammingModelType.Cuda,
        ProgrammingModelType.Rocm,
    ),
    Scaling(ScalingMode.Strong),
):
    variant(
        "workload",
        default="hns-reaxff",
        values=("hns-reaxff", "lj", "eam", "chain", "chute", "rhodo", "pace"),
        description="workloads",
    )

    variant(
        "version",
        default="20251219",
        values=("develop", "20251219", "latest", "20250722"),
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

    variant(
        "apu",
        default=False,
        values=(True, False),
        description="Enable APU support",
    )

    variant(
        "other",
        default=False,
        values=(True, False),
        description="Set other input/environment variables",
    )

    maintainers("simongdg", "rfhaque")

    def compute_applications_section(self):
        if self.spec.satisfies("workload=pace"):
            self.add_experiment_variable("lc", 3.597, True)
            self.add_experiment_variable("lattice", "fcc", True)

        if self.spec.satisfies("exec_mode=test"):
            if self.spec.satisfies("workload=hns-reaxff"):
                total_problem_sizes = {"x": 8, "y": 8, "z": 8}
            if self.spec.satisfies("workload=pace"):
                total_problem_sizes = {"L": 4}
        else:
            if self.spec.satisfies("workload=hns-reaxff"):
                total_problem_sizes = {"x": 20, "y": 40, "z": 32}
            if self.spec.satisfies("workload=pace"):
                total_problem_sizes = {"L": 64}

        self.add_experiment_variable(
            "total_problem_size_dict", total_problem_sizes, True
        )
        input_sizes = " ".join(f"-var {k} {{{k}}}" for k in total_problem_sizes.keys())

        if self.spec.satisfies("workload=pace"):
            self.add_experiment_variable("thermo", "10", True)

        if self.spec.satisfies("+rocm") or self.spec.satisfies("+cuda"):
            kokkos_mode = "g 1"
            kokkos_gpu_aware = "on" if self.spec.satisfies("+gpu-aware-mpi") else "off"
            kokkos_comm = "device"
        else:
            kokkos_mode = "t {n_threads_per_proc}"
            kokkos_gpu_aware = "off"
            kokkos_comm = "host"

        self.add_experiment_variable(
            "lammps_flags",
            f"{input_sizes} -sf kk -k on {kokkos_mode} -pk kokkos gpu/aware {kokkos_gpu_aware} neigh half comm {kokkos_comm} newton on",
            False,
        )

        self.add_experiment_variable("n_resources", 4, False)

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

        if self.spec.satisfies("+rocm"):
            if self.spec.satisfies("+other"):
                self.set_environment_variable("MPICH_OFI_NIC_POLICY", "GPU")
                self.set_environment_variable("FI_HMEM", "rocr")
                self.set_environment_variable("HUGETLB_MORECORE", "yes")
                self.set_environment_variable("HUGETLB_RESTRICT_EXE", "defrag:lmp")
                self.set_environment_variable("HSA_XNACK", 1)

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

        if self.spec.satisfies("exec_mode=test"):
            self.add_experiment_variable("timesteps", 100, False)
        else:
            self.add_experiment_variable("timesteps", 10000000, False)

        if self.spec.satisfies("workload=pace"):
            self.add_experiment_variable(
                "input_file", "{input_path}/in.pace.product", False
            )
            self.set_required_variables(
                process_problem_size="{L}*{L}*{L}*4/{n_resources}",  # placeholder value using fcc lattice with 4 atoms per unit cell
                total_problem_size="{L}*{L}*{L}*4",  # placeholder value using fcc lattice with 4 atoms per unit cell
            )
        if self.spec.satisfies("workload=hns-reaxff"):
            self.add_experiment_variable(
                "input_file", "{input_path}/in.reaxff.hns", False
            )

            self.set_required_variables(
                process_problem_size="{x}*{y}*{z}/{n_resources}",
                total_problem_size="{x}*{y}*{z}",
            )

    def compute_package_section(self):
        fft = self.spec.variants["fft"][0]
        fft_kokkos = self.spec.variants["fft_kokkos"][0]
        if self.spec.satisfies("+cuda"):
            fft_kokkos = "cufft"
        if self.spec.satisfies("+rocm"):
            fft_kokkos = "hipfft"
            if self.spec.satisfies("+apu"):
                apu = "+apu"
            else:
                apu = "~apu"

        pace = "+ml-pace" if self.spec.satisfies("workload=pace") else "~ml-pace"

        self.add_package_spec(
            self.name,
            [
                f"lammps{self.determine_version()} +opt+manybody+molecule+kspace+rigid+kokkos+asphere+dpd-basic+dpd-meso+dpd-react+dpd-smooth+reaxff lammps_sizes=bigbig {pace} fft_kokkos={fft_kokkos} {apu}"
            ],
        )
