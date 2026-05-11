# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType


class Babelstream(
    Experiment,
    Caliper,
    ProgrammingModel(
        ProgrammingModelType.Openmp,
        ProgrammingModelType.Cuda,
        ProgrammingModelType.Rocm,
    ),
):
    variant(
        "workload",
        default="babelstream",
        description="babelstream",
    )

    variant(
        "version",
        default="caliper",
        values=("develop", "latest", "5.0", "caliper"),
        description="app version",
    )

    maintainers("daboehme")

    def compute_applications_section(self):
        self.add_experiment_variable("n", "50", True)
        self.add_experiment_variable("s", "10240000", True)

        self.add_experiment_variable("n", "35", False)
        self.add_experiment_variable("o", "0", False)
        self.add_experiment_variable("n_nodes", 1, True)

        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("execute", "cuda-stream", False)
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("execute", "hip-stream", False)
        else:
            self.add_experiment_variable("execute", "omp-stream", False)

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 16, True)
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_nodes}*{sys_gpus_per_node}")
            n_resources = "{n_gpus}"
        else:
            self.add_experiment_variable("n_ranks", "{n_nodes}*{sys_cores_per_node}")
            n_resources = "{n_ranks}"

        self.set_required_variables(
            n_resources=f"{n_resources}",
            process_problem_size="{s}",
            total_problem_size="{s} * {n_resources}",
        )

    def compute_package_section(self):
        # get package version
        omp_spec = "+omp" if self.spec.satisfies("+openmp") else ""
        hip_spec = "+hip" if self.spec.satisfies("+rocm") else ""
        self.add_package_spec(
            self.name, [f"babelstream{self.determine_version()} {omp_spec} {hip_spec}"]
        )
