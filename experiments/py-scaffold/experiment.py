# Copyright 2024 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0
#
# Test

import math

from benchpark.caliper import Caliper
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
from benchpark.scaling import Scaling, ScalingMode


class PyScaffold(
    Experiment,
    ProgrammingModel(ProgrammingModelType.Cuda, ProgrammingModelType.Rocm),
    Scaling(ScalingMode.Strong, ScalingMode.Weak),
    Caliper,
):

    maintainers("michaelmckinsey1")

    variant(
        "workload",
        default="sweep",
        values=("sweep",),
    )

    variant("version", default="main", values=("main",), description="app version")

    def compute_applications_section(self):

        n_gpus = 4
        config_url = "https://raw.githubusercontent.com/LBANN/ScaFFold/refs/heads/main/ScaFFold/configs/benchmark_default.yml"
        batch_size = 1
        sharding = [1, 1, 1]
        shards = math.prod(sharding)

        if self.spec.satisfies("exec_mode=test"):
            epochs = 10
            problem_scale = 6
        else:
            epochs = -1
            problem_scale = 7

        if self.spec.satisfies("+strong"):
            batch_size = "{n_gpus} * {scaling_factor}**{scaling_iterations}"

        self.add_experiment_variable("n_gpus", n_gpus, True)
        self.add_experiment_variable("problem_scale", problem_scale, True)
        self.add_experiment_variable("num_epochs", epochs, True)
        self.add_experiment_variable("batch_size", batch_size, True)
        self.add_experiment_variable("sharding", sharding, False)
        self.add_experiment_variable("shards", shards, False)

        self.add_experiment_variable("config_url", config_url, False)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_gpus": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "batch_size": lambda var, itr, dim, scaling_factor: var.val(dim)
                    / scaling_factor,
                },
                ScalingMode.Weak: {
                    "n_gpus": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "batch_size": lambda var, itr, dim, scaling_factor: var.val(dim),
                },
            }
        )

        self.set_required_variables(
            n_resources="{n_gpus}",
            process_problem_size="{batch_size}/{shards}",
            total_problem_size="{batch_size}*{n_gpus}/{shards}",
        )

    def compute_package_section(self):
        if self.spec.variants["package_manager"][0] != "spack-pip":
            raise ValueError(
                "Use the 'spack-pip' package manager for this benchmark. Set 'package_manager=spack-pip'"
            )
        elif self.spec.variants["allocation"][0] != "torchrun-hpc":
            raise ValueError(
                "Use the 'torchrun-hpc' launcher mode for this benchmark. Set 'allocation=torchrun-hpc'"
            )

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
                f"--extra-index-url https://download.pytorch.org/whl/\n--extra-index-url https://pypi.org/simple\nScaFFold[{model}] @ git+https://github.com/LBANN/ScaFFold.git",
            ],
            package_manager="pip",
        )
