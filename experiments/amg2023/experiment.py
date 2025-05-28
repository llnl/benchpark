# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.scaling import StrongScaling
from benchpark.scaling import WeakScaling
from benchpark.scaling import ThroughputScaling
from benchpark.caliper import Caliper


class Amg2023(
    Experiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    StrongScaling,
    WeakScaling,
    ThroughputScaling,
    Caliper,
):
    variant(
        "workload",
        default="problem1",
        values=("problem1", "problem2"),
        description="problem1 or problem2",
    )

    variant(
        "version",
        default="develop",
        description="app version",
    )

    maintainers("pearce8")

    # requires("system+papi", when(caliper=topdown*))

    # TODO: Support list of 3-tuples
    # variant(
    #     "p",
    #     description="value of p",
    # )

    # TODO: Support list of 3-tuples
    # variant(
    #     "n",
    #     description="value of n",
    # )

    def compute_applications_section(self):
        # TODO: Replace with conflicts clause
        scaling_modes = {
            "strong": self.spec.satisfies("+strong"),
            "weak": self.spec.satisfies("+weak"),
            "throughput": self.spec.satisfies("+throughput"),
            "single_node": self.spec.satisfies("+single_node"),
        }

        scaling_mode_enabled = [key for key, value in scaling_modes.items() if value]
        if len(scaling_mode_enabled) != 1:
            raise BenchparkError(
                f"Only one type of scaling per experiment is allowed for application package {self.name}"
            )

        # Number of processes in each dimension
        num_procs = {"px": 2, "py": 2, "pz": 2}

        # Per-process size (in zones) in each dimension
        problem_sizes = {"nx": 80, "ny": 80, "nz": 80}

        if self.spec.satisfies("+single_node"):
            n_resources = 1
            # TODO: Check if n_ranks / n_resources_per_node <= 1
            for pk, pv in num_procs.items():
                self.add_experiment_variable(pk, pv, True)
                n_resources *= pv
            for nk, nv in problem_sizes.items():
                self.add_experiment_variable(nk, nv, True)
        elif self.spec.satisfies("+throughput"):
            n_resources = 1
            for pk, pv in num_procs.items():
                self.add_experiment_variable(pk, pv, True)
                n_resources *= pv
            scaled_variables = self.generate_throughput_scaling_params(
                {tuple(problem_sizes.keys()): list(problem_sizes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for nk, nv in scaled_variables.items():
                self.add_experiment_variable(nk, nv, True)
        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(num_procs.keys()): list(num_procs.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for pk, pv in scaled_variables.items():
                self.add_experiment_variable(pk, pv, True)
            n_resources = [
                x * y * z
                for x, y, z in zip(
                    *(scaled_variables[p] for p in num_procs if p in scaled_variables)
                )
            ]
            # Notice 1/scaling-factor to keep total problem size constant for per-process problem size experiments
            scaled_problem_sizes = self.generate_strong_scaling_params(
                {tuple(problem_sizes.keys()): list(problem_sizes.values())},
                1 / int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for nk, nv in scaled_problem_sizes.items():
                self.add_experiment_variable(nk, nv, True)
        elif self.spec.satisfies("+weak"):
            # Use "strong scaling" to generate resource scaling since problem size is per-process
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
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)
            for nk, nv in problem_sizes.items():
                self.add_experiment_variable(nk, nv, True)

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", n_resources, True)
        else:
            self.add_experiment_variable("n_ranks", n_resources, True)

        self.set_required_variables(
            n_resources="{px}*{py}*{pz}",
            process_problem_size="{nx}*{ny}*{nz}",
            total_problem_size="{nx}*{ny}*{nz}*{px}*{py}*{pz}",
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"amg2023@{app_version} +mpi"])
