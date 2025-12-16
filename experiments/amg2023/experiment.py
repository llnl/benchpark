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

    maintainers("pearce8")

    def generate_perf_specs(self):
        # Add problem specs as needed here
        if self.spec.satisfies("+throughput"):
            problem_spec = {
                "nx": [50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270],
                "ny": [50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270],
                "nz": [50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270],
                "pool_size": [1, 2, 3, 3, 4, 5, 6, 8, 9, 11, 13, 16, 18, 21, 24, 28, 32, 36, 42, 46, 50, 64, 64],
                "px" : 1,
                "py" : 1,
                "pz" : 1,
                "strong_n": None,
                "strong_p": None,
                "weak_n": None,
                "weak_p": None,
                "throughput_n": None,
                "throughput_p": None,
            }
            problem_spec["px"] = [problem_spec["px"]] * len(problem_spec["nx"])
            problem_spec["py"] = [problem_spec["py"]] * len(problem_spec["ny"])
            problem_spec["pz"] = [problem_spec["pz"]] * len(problem_spec["nz"])
            #problem_spec = {
            #    "nx": 50,
            #    "ny": 50,
            #    "nz": 50,
            #    "pool_size": [1, 2, 3, 3, 4, 5, 6, 8, 9, 11, 13, 16, 18, 21, 24, 28, 32, 36, 42, 46, 50, 64, 64],
            #    "px" : 1,
            #    "py" : 1,
            #    "pz" : 1,
            #    "strong_n": None,
            #    "strong_p": None,
            #    "weak_n": None,
            #    "weak_p": None,
            #    "throughput_n": lambda var, itr, dim, scaling_factor: [50+(itr+1)*10, 50+(itr+1)*10, 50+(itr+1)*10],
            #    "throughput_p": lambda var, itr, dim, scaling_factor: var.val(dim),
            #}
        elif self.spec.satisfies("+strong"):
            problem_spec = {
                "nx": 270,
                "ny": 270,
                "nz": 270,
                "pool_size": 64,
                "px": 1,
                "py": 1,
                "pz": 1,
                "strong_n": lambda var, itr, dim, scaling_factor: var.val(dim) // scaling_factor,
                "strong_p": lambda var, itr, dim, scaling_factor: var.val(dim) * scaling_factor,
                "weak_n": None,
                "weak_p": None,
                "throughput_n": None,
                "throughput_p": None,
            }
        elif self.spec.satisfies("+weak"):
            # High - SPX
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
                "weak_p": lambda var, itr, dim, scaling_factor: var.val(dim) * scaling_factor,
                "throughput_n": None,
                "throughput_p": None,
            }
            # High - CPX
            #problem_spec = {
            #    "nx": 94,
            #    "ny": 94,
            #    "nz": 94,
            #    "pool_size": 3,
            #    "px": 1,
            #    "py": 1,
            #    "pz": 1,
            #    "strong_n": None,
            #    "strong_p": None,
            #    "weak_n": lambda var, itr, dim, scaling_factor: var.val(dim),
            #    "weak_p": lambda var, itr, dim, scaling_factor: var.val(dim) * scaling_factor,
            #    "throughput_n": None,
            #    "throughput_p": None,
            #}
            # Low - SPX
            #problem_spec = {
            #    "nx": 86,
            #    "ny": 86,
            #    "nz": 86,
            #    "pool_size": 2,
            #    "px": 1,
            #    "py": 1,
            #    "pz": 1,
            #    "strong_n": None,
            #    "strong_p": None,
            #    "weak_n": lambda var, itr, dim, scaling_factor: var.val(dim),
            #    "weak_p": lambda var, itr, dim, scaling_factor: var.val(dim) * scaling_factor,
            #    "throughput_n": None,
            #    "throughput_p": None,
            #}
            # Low - CPX
            #problem_spec = {
            #    "nx": 48,
            #    "ny": 48,
            #    "nz": 48,
            #    "pool_size": 1,
            #    "px": 1,
            #    "py": 1,
            #    "pz": 1,
            #    "strong_n": None,
            #    "strong_p": None,
            #    "weak_n": lambda var, itr, dim, scaling_factor: var.val(dim),
            #    "weak_p": lambda var, itr, dim, scaling_factor: var.val(dim) * scaling_factor,
            #    "throughput_n": None,
            #    "throughput_p": None,
            #}
        else:
            problem_spec = {
                "nx": [128, 256],
                "ny": [128, 256],
                "nz": [128, 256],
                "pool_size": [9, 64],
                "px": [2, 2],
                "py": [2, 2],
                "pz": [2, 2],
                "strong_n": lambda var, itr, dim, scaling_factor: var.val(dim) // scaling_factor,
                "strong_p": lambda var, itr, dim, scaling_factor: var.val(dim) * scaling_factor,
                "weak_n": lambda var, itr, dim, scaling_factor: var.val(dim),
                "weak_p": lambda var, itr, dim, scaling_factor: var.val(dim) * scaling_factor,
                "throughput_n": lambda var, itr, dim, scaling_factor: var.val(dim) * scaling_factor,
                "throughput_p": lambda var, itr, dim, scaling_factor: var.val(dim),
            }

        # Per-process size (in zones) in each dimension
        self.add_experiment_variable("process_problem_size_dict", {
            "nx": problem_spec["nx"],
            "ny": problem_spec["ny"], 
            "nz": problem_spec["nz"], 
        }, True)

        # Umpire device pool size
        self.add_experiment_variable("pool", problem_spec["pool_size"], True)

        # Number of processes in each dimension
        self.add_experiment_variable("n_resources_dict", {
            "px": problem_spec["px"],
            "py": problem_spec["py"],
            "pz": problem_spec["pz"],
        }, True)

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
