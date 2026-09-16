# Copyright 2026 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType


class HecbenchNbody(
    Experiment,
    ProgrammingModel(ProgrammingModelType.Cuda, ProgrammingModelType.Rocm),
):
    variant(
        "workload",
        default="nbody",
        values=("nbody",),
        description="HeCBench N-body workload",
    )
    variant(
        "version",
        default="2026-08-13",
        values=("2026-08-13",),
        description="Pinned HeCBench source version",
    )

    maintainers("chung38")

    def __init__(self, spec):
        super().__init__(spec)
        self.name = "hecbench-nbody"

    def compute_applications_section(self):
        model = "hip" if self.spec.satisfies("+rocm") else "cuda"
        if self.spec.satisfies("exec_mode=test"):
            particle_count, integration_steps = 256, 3
        else:
            particle_count, integration_steps = 4096, 10

        self.add_experiment_variable("model", model, True)
        self.add_experiment_variable("particle_count", particle_count, True)
        self.add_experiment_variable("integration_steps", integration_steps, True)
        self.add_experiment_variable("n_nodes", 1, False)
        self.add_experiment_variable("n_ranks", 1, False)
        self.add_experiment_variable("n_gpus", 1, False)
        self.set_required_variables(
            n_resources="1",
            process_problem_size="{particle_count}",
            total_problem_size="{particle_count}",
        )

    def compute_package_section(self):
        self.add_package_spec(
            self.name,
            [f"hecbench{self.determine_version()} benchmark=nbody ~caliper "],
        )
