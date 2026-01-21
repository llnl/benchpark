# Copyright 2024 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import Scaling, ScalingMode


class PyScaffold(
    Experiment,
    CudaExperiment,
    ROCmExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak),
    Caliper,
):

    maintainers("michaelmckinsey1")

    variant(
        "workload",
        default="sweep",
        values=("sweep",),
    )

    variant("version", default="main", values=("main"), description="app version")

    def compute_applications_section(self):
        if self.spec.satisfies("+strong"):
            n_gpus = 4
            if self.spec.satisfies("exec_mode=test"):
                problem_scale = 5
            else:
                problem_scale = 6
        elif self.spec.satisfies("+weak"):
            n_gpus = 1
            problem_scale = 5
        else:
            n_gpus = 1
            problem_scale = 6

        self.add_experiment_variable("n_gpus", n_gpus, True)
        self.add_experiment_variable("problem_scale", problem_scale, True)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_gpus": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "problem_scale": lambda var, itr, dim, scaling_factor: var.val(dim),
                },
                ScalingMode.Weak: {
                    "n_gpus": lambda var, itr, dim, scaling_factor: var.val(dim) * 2**3,
                    "problem_scale": lambda var, itr, dim, scaling_factor: var.val(dim)
                    + 1,
                },
            }
        )

        self.set_required_variables(
            n_resources="{n_gpus}",
            process_problem_size="({problem_scale}-4)/({n_gpus}/({problem_scale}-4)**3)",
            total_problem_size="{problem_scale}",
        )

    def compute_package_section(self):
        # Spec that will be written into requirements.txt for pip install
        sys_name = self.system_spec._name
        if self.spec.satisfies("+rocm"):
            if "llnl" in sys_name:
                # site-specific wheel for rocm
                model = "rocmwci"
            else:
                model = "rocm"
        elif self.spec.satisfies("+cuda"):
            model = "cuda"
        self.add_package_spec(
            self.name,
            [f"py-scaffold@{self.spec.variants['version'][0]}"],
            package_manager="spack",
        )
        self.add_package_spec(
            self.name,
            [
                # extra index for torch wheel and pypi index for packages that won't be found on WCI
                f"--extra-index-url https://download.pytorch.org/whl/\n--extra-index-url https://pypi.org/simple\ngit+https://github.com/LBANN/ScaFFold.git[{model}]",
            ],
            package_manager="pip",
        )
