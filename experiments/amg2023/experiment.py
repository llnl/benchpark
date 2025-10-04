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
from benchpark.caliper import Caliper


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

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            process_problem_size_dict = {"nx": 80, "ny": 80, "nz": 80}
            n_resources_dict = {"px": 2, "py": 2, "pz": 2}
        else:
            process_problem_size_dict = {
                "nx": [128, 256],
                "ny": [128, 256],
                "nz": [128, 256],
            }
            n_resources_dict = {"px": [2, 2], "py": [2, 2], "pz": [2, 2]}

        # Per-process size (in zones) in each dimension
        self.add_experiment_variable(
            "process_problem_size_dict", process_problem_size_dict, True
        )

        # Number of processes in each dimension
        self.add_experiment_variable("n_resources_dict", n_resources_dict, True)

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{px}*{py}*{pz}",
            process_problem_size="{nx}*{ny}*{nz}",
            total_problem_size="{nx}*{ny}*{nz}*{px}*{py}*{pz}",
        )

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
                self.name, [f"amg2023{self.determine_version()} +umpire {mixedint} {gam}"]
            )
        else:
            self.add_package_spec(
                self.name, [f"amg2023{self.determine_version()} {mixedint}"]
            )
        self.add_package_spec("hypre", ["hypre+lapack"])
