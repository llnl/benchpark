# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.rocm import ROCmExperiment


class Babelstream(
    Experiment,
    Caliper,
    CudaExperiment,
    ROCmExperiment,
    OpenMPExperiment,
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

        self.add_experiment_variable("processes_per_node", "1", True)
        self.add_experiment_variable("n", "35", False)
        self.add_experiment_variable("o", "0", False)
        n_resources = 1

        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("execute", "cuda-stream", False)
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("execute", "hip-stream", False)
        else:
            self.add_experiment_variable("execute", "omp-stream", False)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", n_resources, True)
        else:
            self.add_experiment_variable("n_ranks", n_resources, True)

        self.set_required_variables(
            n_resources=f"{n_resources}",
            process_problem_size="{n}/" + str(n_resources),
            total_problem_size="{n}",
        )

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"babelstream{self.determine_version()}"])
