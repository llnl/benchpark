# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType

XsbenchProgrammingModel = ProgrammingModel(
    ProgrammingModelType.Cuda,
    ProgrammingModelType.Rocm,
)


class Xsbench(
    Experiment,
    XsbenchProgrammingModel,
):
    variant(
        "workload",
        default="event",
        values=("event",),
        description="Which Ramble workload to execute.",
    )

    variant(
        "version",
        default="20",
        values=("20", "latest"),
        description="Which XSBench version to use.",
    )

    maintainers("matthewc2003")

    def compute_applications_section(self):
        # Minimal validated configuration: one process on one GPU.
        self.add_experiment_variable("n_nodes", 1, True)
        self.add_experiment_variable("n_gpus", 1, False)

        # Override the event workload defaults from application.py.
        self.add_experiment_variable("benchmark_size", "large", True)
        self.add_experiment_variable("grid_type", "unionized", True)
        self.add_experiment_variable("lookups", "17000000", True)
        self.add_experiment_variable("kernel", "0", True)

        # Required Benchpark experiment metadata.
        self.set_required_variables(
            n_resources="{n_gpus}",
            process_problem_size="{lookups}",
            total_problem_size="{lookups}",
        )

    def compute_package_section(self):
        # Keep a trailing space: Benchpark appends programming-model Spack
        # variants directly to this string.
        self.add_package_spec(
            self.name,
            [f"benchpark.xsbench{self.determine_version()} " "~mpi ~openmp "],
        )
