# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
from benchpark.scaling import Scaling, ScalingMode


class Laghos(
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
        default="sedov",
        values=(
            "taylor-green",
            "sedov",
            "1D-sod-shock",
            "triple-point",
            "gresho-vortex",
            "2D-riemann-12",
            "2D-riemann-6",
            "2D-rayleigh-taylor",
        ),
        description="problem type",
    )

    variant(
        "order",
        default="linear",
        values=("linear", "quadratic", "cubic"),
        description="solution order",
    )

    variant(
        "version",
        default="develop",
        description="app version",
    )

    variant(
        "gpu-aware-mpi",
        default=False,
        values=(True, False),
        description="Use GPU-aware MPI",
    )

    variant(
        "nc",
        default=False,
        values=(True, False),
        description="nonconforming or conforming",
    )

    variant(
        "raja",
        default=True,
        values=(True, False),
        description="Use RAJA backend for MFEM",
    )

    variant(
        "visualizations",
        default=False,
        values=(True, False),
        description="Enable or disable GLVis and VIsit visualizations",
    )

    variant(
        "dim",
        default="3",
        values=("1", "2", "3"),
        description="Dimension of the problem",
    )

    variant(
        "ms",
        default="250",
        description="Maximum number of steps (negative means no restriction).",
    )

    variant(
        "tf",
        default="10000",
        description="Final time; start time is 0.",
    )

    variant(
        "s",
        default="4",
        values=("1", "2", "3", "4", "6", "7"),
        description="ODE solver type",
    )

    maintainers("wdhawkins")

    def generate_perf_specs(self):
        problem_spec = {
            "nx": 1,
            "ny": 1,
            "nz": 1,
            "pool_size": 16,
            "resource_count": 4,
            "strong": None,
            "weak": None,
            "throughput": None,
        }
        # Add problem specs as needed here
        if self.spec.satisfies("+throughput"):
            if self.spec.satisfies("order=linear"):
                problem_spec["rs"] = [4, 4, 4]
                problem_spec["rp"] = [2, 3, 4]
            elif self.spec.satisfies("order=quadratic"):
                problem_spec["rs"] = [4, 4, 4]
                problem_spec["rp"] = [1, 2, 3]
            elif self.spec.satisfies("order=cubic"):
                problem_spec["rs"] = [4, 4, 4]
                problem_spec["rp"] = [1, 2, 3]
        elif self.spec.satisfies("+strong"):
            problem_spec["strong"] = (
                lambda var, itr, dim, scaling_factor: var.val(dim) * scaling_factor
            )
            if self.spec.satisfies("order=linear"):
                problem_spec["rs"] = 4
                problem_spec["rp"] = 3
            elif self.spec.satisfies("order=quadratic"):
                problem_spec["rs"] = 4
                problem_spec["rp"] = 2
            elif self.spec.satisfies("order=cubic"):
                problem_spec["rs"] = 4
                problem_spec["rp"] = 1
        elif self.spec.satisfies("+weak"):
            problem_spec["nx"] = [1, 2, 3, 4, 5, 6]
            problem_spec["ny"] = [1, 2, 3, 4, 5, 6]
            problem_spec["nz"] = [1, 2, 3, 4, 5, 6]
            problem_spec["resource_count"] = [4, 32, 108, 256, 500, 864]
            if self.spec.satisfies("order=linear"):
                problem_spec["rs"] = 4
                problem_spec["rp"] = 3
            elif self.spec.satisfies("order=quadratic"):
                problem_spec["rs"] = 4
                problem_spec["rp"] = 2
            elif self.spec.satisfies("order=cubic"):
                problem_spec["rs"] = 4
                problem_spec["rp"] = 1
        else:
            problem_spec["rs"] = 4
            problem_spec["rp"] = 1

        self.add_experiment_variable("nx", problem_spec["nx"], True)
        self.add_experiment_variable("ny", problem_spec["ny"], True)
        self.add_experiment_variable("nz", problem_spec["nz"], True)
        self.add_experiment_variable("rs", problem_spec["rs"], True)
        self.add_experiment_variable("rp", problem_spec["rp"], True)

        self.add_experiment_variable(
            "resource_count", problem_spec["resource_count"], True
        )

        # Per-process size (in zones) in each dimension
        self.add_experiment_variable("zones", "{nx}*{ny}*{nz}*(8**({rs}+{rp}))", False)

        # Umpire device pool size
        self.add_experiment_variable("pool", problem_spec["pool_size"], False)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "resource_count": problem_spec["strong"],
                },
                ScalingMode.Weak: {
                    "resource_count": problem_spec["weak"],
                },
                ScalingMode.Throughput: {
                    "resource_count": problem_spec["throughput"],
                },
            }
        )

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=perf"):
            self.generate_perf_specs()
        else:
            # "zones" defined from mesh file, we are hardcoding it here
            self.add_experiment_variable("nx", 1, True)
            self.add_experiment_variable("ny", 1, True)
            self.add_experiment_variable("nz", 1, True)

            self.add_experiment_variable("rs", 3, True)
            self.add_experiment_variable("rp", 2, True)
            self.add_experiment_variable(
                "zones", "{nx}*{ny}*{nz}*(8**({rs}+{rp}))", False
            )
            self.add_experiment_variable("pool", 16, True)
            # resource_count is the number of resources used for this experiment:
            self.add_experiment_variable("resource_count", 1, False)

            # Register the scaling variables and their respective scaling functions
            # required to correctly scale the experiment for the given scaliing policy
            # Strong scaling scales up resource_count by the specified scaling_factor
            self.register_scaling_config(
                {
                    ScalingMode.Strong: {
                        "resource_count": lambda var, itr, dim, scaling_factor: var.val(
                            dim
                        )
                        * scaling_factor,
                    },
                    ScalingMode.Weak: {
                        "resource_count": None,
                    },
                    ScalingMode.Throughput: {
                        "resource_count": None,
                    },
                }
            )

        if self.spec.satisfies("order=linear"):
            self.add_experiment_variable("order", "linear", True)
            self.add_experiment_variable("ok", 1, False)
            self.add_experiment_variable("ot", 0, False)
        elif self.spec.satisfies("order=quadratic"):
            self.add_experiment_variable("order", "quadratic", True)
            self.add_experiment_variable("ok", 2, False)
            self.add_experiment_variable("ot", 1, False)
        elif self.spec.satisfies("order=cubic"):
            self.add_experiment_variable("order", "cubic", True)
            self.add_experiment_variable("ok", 3, False)
            self.add_experiment_variable("ot", 2, False)
        else:
            self.add_experiment_variable("order", "linear", True)
            self.add_experiment_variable("ok", 1, False)
            self.add_experiment_variable("ot", 0, False)

        if self.spec.satisfies("+nc"):
            self.add_experiment_variable("nc_type", "nonconforming", True)
            self.add_experiment_variable("nc", "-nc", False)
        else:
            self.add_experiment_variable("nc_type", "conforming", True)
            self.add_experiment_variable("nc", "-no-nc", False)

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{resource_count}",
            process_problem_size="{zones} / {n_resources}",
            total_problem_size="{zones}",
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

        if self.spec.satisfies("+visualizations"):
            self.add_experiment_variable("vis", "-vis", True)
            self.add_experiment_variable("vs", "-visit", True)
            self.add_experiment_variable(
                "k", "-k {experiment_run_dir}/VISUALIZATION_OUTPUT/", False
            )
        else:
            self.add_experiment_variable("vis", "-no-vis", True)
            self.add_experiment_variable("vs", "-no-visit", True)
            self.add_experiment_variable("k", "", False)

        self.add_experiment_variable("dim", self.spec.variants["dim"][0], True)
        self.add_experiment_variable("ms", self.spec.variants["ms"][0], True)
        self.add_experiment_variable("tf", self.spec.variants["tf"][0], True)
        self.add_experiment_variable("s", self.spec.variants["s"][0], True)

    def compute_package_section(self):
        gam = "~gpu-aware-mpi"
        raja = "~raja"
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            if self.spec.satisfies("+gpu-aware-mpi"):
                gam = "+gpu-aware-mpi"
        if self.spec.satisfies("+raja"):
            raja = "+raja"
        self.add_package_spec(
            self.name, [f"laghos{self.determine_version()} +metis {gam} {raja}"]
        )
        self.add_package_spec("hypre", ["hypre@2.32.0: +lapack"])
