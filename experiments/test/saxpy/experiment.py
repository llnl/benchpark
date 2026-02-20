# Copyright 2024 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.caliper import Caliper
from benchpark.cuda import CudaExperiment
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.rocm import ROCmExperiment


class Saxpy(
    Experiment,
    MpiOnlyExperiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    Caliper,
):
    variant(
        "workload",
        default="problem",
        description="problem",
    )

    variant(
        "version",
        default="1.0.0",
        description="app version",
    )

    maintainers("rfhaque")

    def compute_applications_section(self):
        # GPU tests include some smaller sizes
        n = ["512", "1024"]
        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_nodes", ["1", "2"], named=True)
            # resource_count is the number of resources used for this experiment:
            self.add_experiment_variable("resource_count", "8")
            self.add_experiment_variable(
                "n_threads_per_proc", ["2", "4"], named=True, matrixed=True
            )
        else:
            n = ["128", "256"] + n
            # resource_count is the number of resources used for this experiment:
            self.add_experiment_variable("resource_count", "1")

        self.add_experiment_variable("n", n, named=True, matrixed=True)

        self.set_required_variables(
            n_resources="{resource_count}",
            process_problem_size="{n}/{n_resources}",
            total_problem_size="{n}",
        )

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"saxpy{self.determine_version()}"])
