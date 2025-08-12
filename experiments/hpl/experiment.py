# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.scaling import StrongScaling
from benchpark.scaling import WeakScaling
from benchpark.openmp import OpenMPExperiment
from benchpark.caliper import Caliper


class Hpl(
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
        description="workload to use",
    )

    variant(
        "version",
        default="2.3-caliper",
        description="app version",
    )

    maintainers("daboehme")

    def compute_applications_section(self):
        # Number of initial nodes
        num_nodes = {"n_nodes": 1}
        problem_size = {"Ns": 10000}

        self.add_experiment_variable("N-Grids", 1, False)
        self.add_experiment_variable("Ps", "4 * {n_nodes}", True)
        self.add_experiment_variable("Qs", "8", False)

        self.add_experiment_variable("N-Ns", 1, False)

        self.add_experiment_variable("N-NBs", 1, False)
        self.add_experiment_variable("NBs", 128, False)

        self.add_experiment_variable(
            "n_ranks", "{sys_cores_per_node} * {n_nodes}", False
        )
        self.add_experiment_variable(
            "n_threads_per_proc", ["2"], named=True, matrixed=True
        )

        if self.spec.satisfies("+single_node"):
            for pk, pv in num_nodes.items():
                self.add_experiment_variable(pk, pv, True)
            for pk, pv in problem_size.items():
                self.add_experiment_variable(pk, pv, True)

        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv, True)
            for pk, pv in problem_size.items():
                self.add_experiment_variable(pk, pv, True)
        elif self.spec.satisfies("+weak"):
            scaled_variables = self.generate_weak_scaling_params(
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                {tuple(problem_size.keys()): list(problem_size.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            num_resources = scaled_variables["n_nodes"]
            self.add_experiment_variable("n_nodes", num_resources, True)

            problem_size = scaled_variables["Ns"]
            self.add_experiment_variable("Ns", problem_size, True)

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{Ns}/{n_ranks}",
            total_problem_size="{Ns}",
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"hpl@{app_version}"])
