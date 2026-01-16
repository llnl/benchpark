# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import Scaling, ScalingMode


class Amg2023(
    Experiment,
    MpiOnlyExperiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
    Caliper,
):
    variant(
        "workload",
        default="problem1",
        values=("problem1", "problem2"),
        description="problem1 or problem2",
    )

    variant(
        "version",
        default="develop",
        values=("develop", "latest", "20240511"),
        description="app version",
    )

    variant(
        "other",
        default=False,
        values=(True, False),
        description="Set other input/environment variables",
    )

    variant(
        "mixedint",
        default=False,
        values=(True, False),
        description="Use 64bit integers while reducing memory use",
    )

    variant(
        "gpu-aware-mpi",
        default=False,
        values=(True, False),
        description="Use GPU-aware MPI",
    )

    variant(
        "target",
        default="MI300-SPX",
        values=("MI250", "MI300-SPX", "MI300-CPX", "H100"),
        description="Target system config",
    )

    maintainers("pearce8")

    def generate_perf_specs(self):
        # Add problem specs as needed here
        if self.spec.satisfies("+throughput"):
            if self.spec.satisfies("workload=problem1"):
                problem_spec = {
                    "nx": [
                        50,
                        60,
                        70,
                        80,
                        90,
                        100,
                        110,
                        120,
                        130,
                        140,
                        150,
                        160,
                        170,
                        180,
                        190,
                        200,
                        210,
                        220,
                        230,
                        240,
                        250,
                        260,
                        270,
                    ],
                    "ny": [
                        50,
                        60,
                        70,
                        80,
                        90,
                        100,
                        110,
                        120,
                        130,
                        140,
                        150,
                        160,
                        170,
                        180,
                        190,
                        200,
                        210,
                        220,
                        230,
                        240,
                        250,
                        260,
                        270,
                    ],
                    "nz": [
                        50,
                        60,
                        70,
                        80,
                        90,
                        100,
                        110,
                        120,
                        130,
                        140,
                        150,
                        160,
                        170,
                        180,
                        190,
                        200,
                        210,
                        220,
                        230,
                        240,
                        250,
                        260,
                        270,
                    ],
                    "pool_size": 1,
                    "px": 1,
                    "py": 1,
                    "pz": 1,
                    "strong_n": None,
                    "strong_p": None,
                    "weak_n": None,
                    "weak_p": None,
                    "throughput_n": None,
                    "throughput_p": None,
                }
                if self.spec.satisfies("target=MI300-SPX") or self.spec.satisfies(
                    "target=MI250"
                ):
                    problem_spec["pool_size"] = [
                        1,
                        1,
                        1,
                        2,
                        3,
                        3,
                        4,
                        5,
                        6,
                        8,
                        9,
                        12,
                        14,
                        16,
                        18,
                        21,
                        24,
                        28,
                        31,
                        36,
                        42,
                        46,
                        52,
                    ]
                elif self.spec.satisfies("target=H100"):
                    problem_spec["pool_size"] = [
                        1,
                        1,
                        1,
                        1,
                        2,
                        3,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        10,
                        12,
                        14,
                        15,
                        18,
                        20,
                        23,
                        27,
                        30,
                        33,
                        38,
                    ]
            elif self.spec.satisfies("workload=problem2"):
                problem_spec = {
                    "nx": [
                        80,
                        90,
                        100,
                        110,
                        120,
                        130,
                        140,
                        150,
                        160,
                        170,
                        180,
                        190,
                        200,
                        210,
                        220,
                        230,
                        240,
                        250,
                        260,
                        270,
                        280,
                        290,
                        300,
                        310,
                        320,
                        330,
                        340,
                        350,
                        360,
                    ],
                    "ny": [
                        80,
                        90,
                        100,
                        110,
                        120,
                        130,
                        140,
                        150,
                        160,
                        170,
                        180,
                        190,
                        200,
                        210,
                        220,
                        230,
                        240,
                        250,
                        260,
                        270,
                        280,
                        290,
                        300,
                        310,
                        320,
                        330,
                        340,
                        350,
                        360,
                    ],
                    "nz": [
                        80,
                        90,
                        100,
                        110,
                        120,
                        130,
                        140,
                        150,
                        160,
                        170,
                        180,
                        190,
                        200,
                        210,
                        220,
                        230,
                        240,
                        250,
                        260,
                        270,
                        280,
                        290,
                        300,
                        310,
                        320,
                        330,
                        340,
                        350,
                        360,
                    ],
                    "pool_size": 1,
                    "px": 1,
                    "py": 1,
                    "pz": 1,
                    "strong_n": None,
                    "strong_p": None,
                    "weak_n": None,
                    "weak_p": None,
                    "throughput_n": None,
                    "throughput_p": None,
                }
                problem_spec["pool_size"] = [
                    1,
                    1,
                    1,
                    1,
                    1,
                    2,
                    2,
                    2,
                    3,
                    3,
                    3,
                    4,
                    4,
                    5,
                    6,
                    7,
                    8,
                    8,
                    9,
                    10,
                    11,
                    13,
                    14,
                    15,
                    17,
                    18,
                    20,
                    22,
                    24,
                ]
            problem_spec["px"] = [problem_spec["px"]] * len(problem_spec["nx"])
            problem_spec["py"] = [problem_spec["py"]] * len(problem_spec["ny"])
            problem_spec["pz"] = [problem_spec["pz"]] * len(problem_spec["nz"])
        elif self.spec.satisfies("+strong"):
            problem_spec = {
                "nx": 270,
                "ny": 270,
                "nz": 270,
                "pool_size": 64,
                "px": 1,
                "py": 1,
                "pz": 1,
                "strong_n": lambda var, itr, dim, scaling_factor: var.val(dim)
                // scaling_factor,
                "strong_p": lambda var, itr, dim, scaling_factor: var.val(dim)
                * scaling_factor,
                "weak_n": None,
                "weak_p": None,
                "throughput_n": None,
                "throughput_p": None,
            }
        elif self.spec.satisfies("+weak"):
            problem_spec = {
                "nx": 171,
                "ny": 171,
                "nz": 171,
                "pool_size": 16,
                "px": 1,
                "py": 1,
                "pz": 1,
                "strong_n": None,
                "strong_p": None,
                "weak_n": lambda var, itr, dim, scaling_factor: var.val(dim),
                "weak_p": lambda var, itr, dim, scaling_factor: var.val(dim)
                * scaling_factor,
                "throughput_n": None,
                "throughput_p": None,
            }
            if self.spec.satisfies("workload=problem1"):
                if (
                    self.spec.satisfies("target=MI300-SPX")
                    or self.spec.satisfies("target=MI250")
                    or self.spec.satisfies("target=H100")
                ):
                    problem_spec["nx"] = 171
                    problem_spec["ny"] = 171
                    problem_spec["nz"] = 171
                    problem_spec["pool_size"] = 16
                    # problem_spec["nx"] = 86
                    # problem_spec["ny"] = 86
                    # problem_spec["nz"] = 86
                    # problem_spec["pool_size"] = 2
                elif self.spec.satisfies("target=MI300-CPX"):
                    problem_spec["nx"] = 94
                    problem_spec["ny"] = 94
                    problem_spec["nz"] = 94
                    problem_spec["pool_size"] = 3
                    # problem_spec["nx"] = 48
                    # problem_spec["ny"] = 48
                    # problem_spec["nz"] = 48
                    # problem_spec["pool_size"] = 1
                    problem_spec["px"] = 4
                    problem_spec["py"] = 3
                    problem_spec["pz"] = 2
            elif self.spec.satisfies("workload=problem2"):
                if (
                    self.spec.satisfies("target=MI300-SPX")
                    or self.spec.satisfies("target=MI250")
                    or self.spec.satisfies("target=H100")
                ):
                    problem_spec["nx"] = 292
                    problem_spec["ny"] = 292
                    problem_spec["nz"] = 292
                    problem_spec["pool_size"] = 13
                elif self.spec.satisfies("target=MI300-CPX"):
                    problem_spec["nx"] = 160
                    problem_spec["ny"] = 160
                    problem_spec["nz"] = 160
                    problem_spec["pool_size"] = 3
                    problem_spec["px"] = 4
                    problem_spec["py"] = 3
                    problem_spec["pz"] = 2
        else:
            problem_spec = {
                "nx": [128, 256],
                "ny": [128, 256],
                "nz": [128, 256],
                "pool_size": [9, 64],
                "px": [2, 2],
                "py": [2, 2],
                "pz": [2, 2],
                "strong_n": lambda var, itr, dim, scaling_factor: var.val(dim)
                // scaling_factor,
                "strong_p": lambda var, itr, dim, scaling_factor: var.val(dim)
                * scaling_factor,
                "weak_n": lambda var, itr, dim, scaling_factor: var.val(dim),
                "weak_p": lambda var, itr, dim, scaling_factor: var.val(dim)
                * scaling_factor,
                "throughput_n": lambda var, itr, dim, scaling_factor: var.val(dim)
                * scaling_factor,
                "throughput_p": lambda var, itr, dim, scaling_factor: var.val(dim),
            }

        # Per-process size (in zones) in each dimension
        self.add_experiment_variable(
            "process_problem_size_dict",
            {
                "nx": problem_spec["nx"],
                "ny": problem_spec["ny"],
                "nz": problem_spec["nz"],
            },
            True,
        )

        # Umpire device pool size
        self.add_experiment_variable("pool", problem_spec["pool_size"], True)

        # Number of processes in each dimension
        self.add_experiment_variable(
            "n_resources_dict",
            {
                "px": problem_spec["px"],
                "py": problem_spec["py"],
                "pz": problem_spec["pz"],
            },
            True,
        )

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_resources_dict": problem_spec["strong_p"],
                    "process_problem_size_dict": problem_spec["strong_n"],
                },
                ScalingMode.Weak: {
                    "n_resources_dict": problem_spec["weak_p"],
                    "process_problem_size_dict": problem_spec["weak_n"],
                },
                ScalingMode.Throughput: {
                    "n_resources_dict": problem_spec["throughput_p"],
                    "process_problem_size_dict": problem_spec["throughput_n"],
                },
            }
        )

        if self.spec.satisfies("+other"):
            self.set_environment_variable("HSA_XNACK", 1)
            self.set_environment_variable("HSA_ENABLE_SDMA", 1)
            self.set_environment_variable("HSA_ENABLE_SDMA_COPY_SIZE_OVERRIDE", 0)
            self.set_environment_variable("GPU_FORCE_BLIT_COPY_SIZE", 0)
            self.set_environment_variable("HUGETLB_DEFAULT_PAGE_SIZE", "2M")
            self.set_environment_variable("HUGETLB_MORECORE", "yes")
            self.set_environment_variable("HUGETLB_VERBOSE", 2)

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=perf"):
            self.generate_perf_specs()
        else:
            process_problem_size_dict = {"nx": 80, "ny": 80, "nz": 80}
            n_resources_dict = {"px": 2, "py": 2, "pz": 2}

            # Per-process size (in zones) in each dimension
            self.add_experiment_variable(
                "process_problem_size_dict", process_problem_size_dict, True
            )

            # Number of processes in each dimension
            self.add_experiment_variable("n_resources_dict", n_resources_dict, True)

            # In this application, since the input problem sizes (process_problem_size_dict)
            # are per process sizes, strong scaling the problem implies that
            # as n_resources_dict are scaled up, i.e. (x * scaling_factor),
            # process_problem_size_dict are commensurately scaled down i.e. (x // scaling_factor)

            # For weak scaling, only the n_resources_dict have to be scaled up,
            # process_problem_size_dict remain the same

            self.register_scaling_config(
                {
                    ScalingMode.Strong: {
                        "n_resources_dict": lambda var, itr, dim, scaling_factor: var.val(
                            dim
                        )
                        * scaling_factor,
                        "process_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                            dim
                        )
                        // scaling_factor,
                    },
                    ScalingMode.Weak: {
                        "n_resources_dict": lambda var, itr, dim, scaling_factor: var.val(
                            dim
                        )
                        * scaling_factor,
                        "process_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                            dim
                        ),
                    },
                    ScalingMode.Throughput: {
                        "n_resources_dict": lambda var, itr, dim, scaling_factor: var.val(
                            dim
                        ),
                        "process_problem_size_dict": lambda var, itr, dim, scaling_factor: var.val(
                            dim
                        )
                        * scaling_factor,
                    },
                }
            )

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{px}*{py}*{pz}",
            process_problem_size="{nx}*{ny}*{nz}",
            total_problem_size="{nx}*{ny}*{nz}*{px}*{py}*{pz}",
        )

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        mixedint = "+mixedint" if self.spec.satisfies("+mixedint") else "~mixedint"
        gam = "~gpu-aware-mpi"
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            if self.spec.satisfies("+gpu-aware-mpi"):
                gam = "+gpu-aware-mpi"
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_package_spec(
                self.name,
                [f"amg2023{self.determine_version()} +umpire {mixedint} {gam}"],
            )
        else:
            self.add_package_spec(
                self.name, [f"amg2023{self.determine_version()} {mixedint}"]
            )
        self.add_package_spec("hypre", ["hypre+lapack"])
