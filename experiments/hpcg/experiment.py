# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.scaling import StrongScaling
from benchpark.scaling import WeakScaling
from benchpark.openmp import OpenMPExperiment
from benchpark.caliper import Caliper


class Hpcg(
    Experiment,
    MpiOnlyExperiment,
    StrongScaling,
    WeakScaling,
    OpenMPExperiment,
    Caliper,
):

    variant(
        "workload",
        default="standard",
        description="workload to run",
    )
    variant(
        "version",
        default="caliper",
        values=("3.1", "develop", "caliper"),
        description="app version",
    )

    maintainers("pearce8")

    def compute_applications_section(self):

        problem_sizes = {"mx": 104, "my": 104, "mz": 104}
        num_procs = {"x": 1, "y": 1, "z": 1}
        n_resources = 1

        if self.spec.satisfies("+single_node"):
            for k, v in problem_sizes.items():
                self.add_experiment_variable(k, v, True)

        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(num_procs.keys()): list(num_procs.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            n_resources = [
                x * y * z
                for x, y, z in zip(
                    *(scaled_variables[p] for p in num_procs if p in scaled_variables)
                )
            ]
            for k, v in problem_sizes.items():
                self.add_experiment_variable(k, v, True)

        elif self.spec.satisfies("+weak"):
            scaled_variables = self.generate_weak_scaling_params(
                {tuple(num_procs.keys()): list(num_procs.values())},
                {tuple(problem_sizes.keys()): list(problem_sizes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            n_resources = [
                x * y * z
                for x, y, z in zip(
                    *(scaled_variables[p] for p in num_procs if p in scaled_variables)
                )
            ]
            for k, v in scaled_variables.items():
                if k in problem_sizes:
                    self.add_experiment_variable(k, v, True)

        self.add_experiment_variable("n_ranks", n_resources, True)
        self.add_experiment_variable("n_threads_per_proc", 1, True)
        self.add_experiment_variable("matrix_size", "{mx} {my} {mz}", False)

        self.add_experiment_variable("iterations", "60", False)

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{mx}*{my}*{mz}/{n_ranks}",
            total_problem_size="{mx}*{my}*{mz}",
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"hpcg@{app_version}"])
