# Copyright 2024 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import ScalingMode, Scaling
from benchpark.caliper import Caliper


class PyScaffold(
    Experiment,
    CudaExperiment,
    ROCmExperiment,
    Scaling(ScalingMode.Strong),
    Caliper,
):

    maintainers("michaelmckinsey1")

    variant(
        "workload",
        default="sweep",
        values=("sweep",),
    )

    variant(
        "scaffold_path",
        default=" ",
        description="Path to local repository of ScaFFold (i.e. git clone), since it is private.",
    )

    variant("version", default="develop", description="app version")

    def compute_applications_section(self):
        self.add_experiment_variable(
            "package_path", self.spec.variants["scaffold_path"][0], False
        )
        self.add_experiment_variable("timeout", 720, True)

        self.add_experiment_variable("n_gpus", 4, True)

        self.add_experiment_variable("problem_scale", 6, True)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_gpus": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    )
                    * scaling_factor,
                    "problem_scale": lambda var, itr, dim, scaling_factor: var.val(
                        dim
                    ),
                },
            }
        )

        self.set_required_variables(
            n_resources="{n_gpus}",
            process_problem_size="{problem_scale}/{n_gpus}",
            total_problem_size="{problem_scale}",
        )

    def compute_package_section(self):
        # Spec written into requirements.txt for pip install
        if self.spec.satisfies("+rocm"):
            model = "rocmwci"
        elif self.spec.satisfies("+cuda"):
            model = "cuda"
        self.add_package_spec(
            self.name,
            [
                "py-scaffold@main"
            ],
            package_manager="spack",
        )
        self.add_package_spec(
            self.name,
            [
                # extra index for torch wheel
                f"--extra-index-url https://download.pytorch.org/whl/\n{self.spec.variants['scaffold_path'][0]}[{model}]",
            ],
            package_manager="pip",
        )
