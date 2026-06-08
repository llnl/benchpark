# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
from benchpark.scaling import Scaling, ScalingMode


class Remhos(
    Experiment,
    ProgrammingModel(
        ProgrammingModelType.Mpionly,
        ProgrammingModelType.Cuda,
        ProgrammingModelType.Rocm,
    ),
    Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
    Caliper,
):

    variant(
        "workload",
        default="2d",
        values=("2d", "3d"),
        description="2d or 3d run",
    )

    variant(
        "version",
        default="develop",
        values=("develop", "latest", "1.0"),
        description="app version",
    )

    variant(
        "gpu-aware-mpi",
        default=False,
        values=(True, False),
        description="Use GPU-aware MPI",
    )

    variant(
        "raja",
        default=True,
        values=(True, False),
        description="Use RAJA backend for MFEM",
    )

    maintainers("rfhaque")

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=perf"):
            if self.spec.satisfies("workload=2d"):
                if self.spec.satisfies("+throughput"):
                    self.add_experiment_variable("epm", 1024, True)
                elif self.spec.satisfies("+weak"):
                    self.add_experiment_variable("epm", 131072, True)
                else:
                    self.add_experiment_variable("epm", 1024, True)
                self.add_experiment_variable("o", 3, False)
                self.add_experiment_variable("p", 14, False)
            elif self.spec.satisfies("workload=3d"):
                if self.spec.satisfies("+throughput"):
                    self.add_experiment_variable("epm", 512, True)
                elif self.spec.satisfies("+weak"):
                    self.add_experiment_variable("epm", 131072, True)
                else:
                    self.add_experiment_variable("epm", 512, True)
                self.add_experiment_variable("o", 2, False)
                self.add_experiment_variable("p", 10, False)
        else:
            if self.spec.satisfies("workload=2d"):
                self.add_experiment_variable("epm", 1024, True)
                self.add_experiment_variable("o", 3, False)
                self.add_experiment_variable("p", 14, False)
            elif self.spec.satisfies("workload=3d"):
                self.add_experiment_variable("epm", 512, True)
                self.add_experiment_variable("o", 2, False)
                self.add_experiment_variable("p", 10, False)
        self.add_experiment_variable("dt", -1.0, False)
        self.add_experiment_variable("tf", 0.5, False)
        self.add_experiment_variable("ho", 3, False)
        self.add_experiment_variable("lo", 5, False)
        self.add_experiment_variable("fct", 2, False)
        self.add_experiment_variable("vs", 1, False)
        self.add_experiment_variable("ms", 5, False)

        # resource_count is the number of resources used for this experiment:
        self.add_experiment_variable("resource_count", 4, False)
        if self.spec.satisfies("+throughput"):
            self.add_experiment_variable("pool", 80, False)
        elif self.spec.satisfies("+weak"):
            self.add_experiment_variable("pool", 16, False)
        else:
            self.add_experiment_variable("pool", 16, False)

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{resource_count}",
            process_problem_size="{epm}",
            total_problem_size="{epm} * {n_resources}",
        )

        # Register the scaling variables and their respective scaling functions
        # required to correctly scale the experiment for the given scaliing policy
        # Strong scaling scales up resource_count by the specified scaling_factor
        # and scales epm down by scaling_factor to keep the problem size constant
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "resource_count": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "epm": lambda var, itr, dim, scaling_factor: var.val(dim)
                    // scaling_factor,
                },
                ScalingMode.Weak: {
                    "resource_count": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "epm": lambda var, itr, dim, scaling_factor: var.val(dim),
                },
                ScalingMode.Throughput: {
                    "resource_count": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    ),
                    "epm": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
            }
        )

        if self.spec.satisfies("+cuda"):
            if self.spec.satisfies("+raja"):
                self.add_experiment_variable("device", "raja-gpu", True)
            else:
                self.add_experiment_variable("device", "cuda", True)
        elif self.spec.satisfies("+rocm"):
            if self.spec.satisfies("+raja"):
                self.add_experiment_variable("device", "raja-gpu", True)
            else:
                self.add_experiment_variable("device", "hip", True)
        else:
            self.add_experiment_variable("device", "cpu", True)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
            if self.spec.satisfies("+gpu-aware-mpi"):
                self.add_experiment_variable("gam", "--gpu-aware-mpi")
            else:
                self.add_experiment_variable("gam", "--no-gpu-aware-mpi")
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        gam = "~gpu-aware-mpi"
        raja = "~raja"
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            if self.spec.satisfies("+gpu-aware-mpi"):
                gam = "+gpu-aware-mpi"
        if self.spec.satisfies("+raja"):
            raja = "+raja"
        self.add_package_spec(
            self.name, [f"remhos{self.determine_version()} +metis {gam} {raja}"]
        )
