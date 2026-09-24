# Copyright 2026 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType


class Wmma(
    Experiment,
    ProgrammingModel(
        ProgrammingModelType.Mpionly,
        ProgrammingModelType.Cuda,
        ProgrammingModelType.Rocm,
    ),
):
    variant(
        "workload",
        default="wmma",
        values=("wmma",),
        description="HeCBench WMMA workload",
    )
    variant(
        "version",
        default="2026-08-13",
        values=("2026-08-13",),
        description="Pinned HeCBench source version",
    )
    variant(
        "implementation",
        default="0",
        values=("0", "1"),
        description="WMMA implementation selector",
    )
    variant(
        "replicas",
        default="1",
        values=int,
        description="Independent MPI replica ranks",
    )
    variant(
        "nodes",
        default="1",
        values=int,
        description="Nodes assigned to the replica ranks",
    )

    maintainers("chung38")

    def __init__(self, spec):
        super().__init__(spec)
        self.name = "wmma"

    def compute_applications_section(self):
        model = "hip" if self.spec.satisfies("+rocm") else "cuda"
        implementation = self.spec.variants["implementation"][0]
        if self.spec.satisfies("exec_mode=test"):
            matrix_m, matrix_n, matrix_k, internal_repetitions = 16, 16, 64, 1
            if implementation == "1":
                matrix_m = matrix_n = matrix_k = 64
        else:
            matrix_m, matrix_n, matrix_k, internal_repetitions = 512, 512, 512, 20

        self.add_experiment_variable("model", model, True)
        self.add_experiment_variable("implementation", implementation, True)
        self.add_experiment_variable("matrix_m", matrix_m, True)
        self.add_experiment_variable("matrix_n", matrix_n, True)
        self.add_experiment_variable("matrix_k", matrix_k, True)
        self.add_experiment_variable(
            "internal_repetitions", internal_repetitions, True
        )
        self.add_experiment_variable("verify", 1, False)
        replicas = self.spec.variants["replicas"][0]
        nodes = self.spec.variants["nodes"][0]
        self.add_experiment_variable("n_nodes", nodes, True)
        self.add_experiment_variable("n_ranks", replicas, True)
        self.add_experiment_variable("n_gpus", replicas, True)
        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{matrix_m}*{matrix_n}*{matrix_k}",
            total_problem_size="{matrix_m}*{matrix_n}*{matrix_k}*{n_ranks}",
        )

    def compute_package_section(self):
        self.add_package_spec(
            self.name,
            [f"hecbench{self.determine_version()} benchmark=wmma +mpi ~caliper "],
        )
