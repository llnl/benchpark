# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
from benchpark.scaling import Scaling, ScalingMode


class Kripke(
    Experiment,
    ProgrammingModel(
        ProgrammingModelType.Mpionly,
        ProgrammingModelType.Openmp,
        ProgrammingModelType.Cuda,
        ProgrammingModelType.Rocm,
    ),
    Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
    Caliper,
):
    variant(
        "workload",
        default="kripke",
        values=("kripke",),
        description="problem1 or problem2",
    )

    variant(
        "version",
        default="2025.12.0",
        values=("develop", "latest", "2025.12.0", "2025.07.0", "1.2.7.0"),
        description="app version",
    )

    variant(
        "gpu-aware-mpi",
        default=False,
        values=(True, False),
        description="Enable GPU-aware MPI",
    )

    variant(
        "problem_size",
        default="large",
        values=("large", "medium", "small"),
        description="Problem size",
    )

    variant(
        "chai",
        default=True,
        values=(True, False),
        description="Enable CHAI",
    )

    maintainers("pearce8")

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            # Number of processes in each dimension
            self.add_experiment_variable(
                "n_resources_dict", {"npx": 2, "npy": 2, "npz": 1}, True
            )

            # Per-process size (in zones) in each dimension
            self.add_experiment_variable(
                "total_problem_size_dict", {"nzx": 32, "nzy": 32, "nzz": 16}, True
            )

            self.add_experiment_variable("ngroups", 64, True)
            self.add_experiment_variable("gs", 1, True)
            self.add_experiment_variable("nquad", 128, True)
            self.add_experiment_variable("ds", 128, True)
            self.add_experiment_variable("lorder", 4, True)
            self.add_experiment_variable("pool", 4, True)
            problem_spec = {
                "nzx": 32,
                "nzy": 32,
                "nzz": 16,
                "pool": 4,
                "npx": 2,
                "npy": 2,
                "npz": 1,
                "ngroups": 64,
                "gs": 1,
                "nquad": 128,
                "ds": 128,
                "lorder": 4,
                "layout": "GDZ",
                "strong_n": lambda var, itr, dim, scaling_factor: var.val(dim),
                "strong_p": lambda var, itr, dim, scaling_factor: var.val(dim)
                * scaling_factor,
                "weak_n": lambda var, itr, dim, scaling_factor: var.val(dim)
                * scaling_factor,
                "weak_p": lambda var, itr, dim, scaling_factor: var.val(dim)
                * scaling_factor,
                "throughput_n": lambda var, itr, dim, scaling_factor: var.val(dim)
                * scaling_factor,
                "throughput_p": lambda var, itr, dim, scaling_factor: var.val(dim),
            }
        # Must be exec_mode=perf
        else:
            if self.spec.satisfies("+throughput"):
                problem_spec = {
                    "nzx": [
                        64,
                        80,
                        100,
                        120,
                        140,
                        160,
                        180,
                        200,
                        220,
                        240,
                        260,
                        280,
                        300,
                    ],
                    "nzy": [
                        64,
                        80,
                        100,
                        120,
                        140,
                        160,
                        180,
                        200,
                        220,
                        240,
                        260,
                        280,
                        300,
                    ],
                    "nzz": [
                        32,
                        40,
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
                    ],
                    "pool": 120,
                    "npx": [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                    "npy": [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                    "npz": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                    "ngroups": 48,
                    "gs": 1,
                    "nquad": 80,
                    "ds": 80,
                    "lorder": 4,
                    "layout": "GDZ",
                    "strong_n": None,
                    "strong_p": None,
                    "weak_n": None,
                    "weak_p": None,
                    "throughput_n": None,
                    "throughput_p": None,
                }
            elif self.spec.satisfies("+weak"):
                problem_spec = {
                    "nzx": 80,
                    "nzy": 80,
                    "nzz": 40,
                    "pool": 120,
                    "npx": 2,
                    "npy": 2,
                    "npz": 1,
                    "ngroups": 48,
                    "gs": 1,
                    "nquad": 80,
                    "ds": 80,
                    "lorder": 4,
                    "layout": "GDZ",
                    "strong_n": None,
                    "strong_p": None,
                    "weak_n": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "weak_p": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "throughput_n": None,
                    "throughput_p": None,
                }
                if self.spec.satisfies("problem_size=large"):
                    problem_spec["nzx"] = 220
                    problem_spec["nzy"] = 220
                    problem_spec["nzz"] = 110
                    problem_spec["pool"] = 105
                if self.spec.satisfies("problem_size=medium"):
                    problem_spec["nzx"] = 200
                    problem_spec["nzy"] = 200
                    problem_spec["nzz"] = 100
                    problem_spec["pool"] = 77
                if self.spec.satisfies("problem_size=small"):
                    problem_spec["nzx"] = 188
                    problem_spec["nzy"] = 188
                    problem_spec["nzz"] = 94
                    problem_spec["pool"] = 70
            else:
                problem_spec = {
                    "nzx": 80,
                    "nzy": 80,
                    "nzz": 40,
                    "pool": 120,
                    "npx": 2,
                    "npy": 2,
                    "npz": 1,
                    "ngroups": 48,
                    "gs": 1,
                    "nquad": 80,
                    "ds": 80,
                    "lorder": 4,
                    "layout": "GDZ",
                    "strong_n": lambda var, itr, dim, scaling_factor: var.val(dim),
                    "strong_p": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "weak_n": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "weak_p": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "throughput_n": None,
                    "throughput_p": None,
                }
        # Number of processes in each dimension
        self.add_experiment_variable(
            "n_resources_dict",
            {
                "npx": problem_spec["npx"],
                "npy": problem_spec["npy"],
                "npz": problem_spec["npz"],
            },
            True,
        )

        # Per-process size (in zones) in each dimension
        self.add_experiment_variable(
            "total_problem_size_dict",
            {
                "nzx": problem_spec["nzx"],
                "nzy": problem_spec["nzy"],
                "nzz": problem_spec["nzz"],
            },
            True,
        )

        self.add_experiment_variable("ngroups", problem_spec["ngroups"], True)
        self.add_experiment_variable("gs", problem_spec["gs"], True)
        self.add_experiment_variable("nquad", problem_spec["nquad"], True)
        self.add_experiment_variable("ds", problem_spec["ds"], True)
        self.add_experiment_variable("lorder", problem_spec["lorder"], True)
        self.add_experiment_variable("layout", problem_spec["layout"], True)
        self.add_experiment_variable("pool", problem_spec["pool"], True)

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{npx}*{npy}*{npz}",
            process_problem_size="({nzx}*{nzy}*{nzz})/({npx}*{npy}*{npz})",
            total_problem_size="{nzx}*{nzy}*{nzz}",
        )

        # In this application, since the input problem sizes (total_problem_size_dict)
        # are global process sizes, strong scaling the problem requires that
        # only n_resources_dict are scaled up, i.e. (x * scaling_factor),
        # total_problem_size_dict remain unchanged

        # For weak scaling, both n_resources_dict and total_problem_size_dict
        # have to be scaled up i.e. (x * scaling_factor)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_resources_dict": problem_spec["strong_p"],
                    "total_problem_size_dict": problem_spec["strong_n"],
                },
                ScalingMode.Weak: {
                    "n_resources_dict": problem_spec["weak_p"],
                    "total_problem_size_dict": problem_spec["weak_n"],
                },
                ScalingMode.Throughput: {
                    "n_resources_dict": problem_spec["throughput_p"],
                    "total_problem_size_dict": problem_spec["throughput_n"],
                },
            }
        )

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("arch", "OpenMP")
        elif self.spec.satisfies("+cuda"):
            self.add_experiment_variable("arch", "CUDA")
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("arch", "HIP")
        else:
            self.add_experiment_variable("arch", "Sequential")

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        gam = (
            "+gpu-aware-mpi"
            if self.spec.variants["gpu-aware-mpi"][0]
            else "~gpu-aware-mpi"
        )
        chai = (
            "+chai"
            if self.spec.variants["chai"][0]
            else "~chai"
        )
        self.add_package_spec(
            self.name, [f"kripke{self.determine_version()} {gam} {chai} +mpi"]
        )
