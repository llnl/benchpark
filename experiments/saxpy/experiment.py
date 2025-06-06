# Copyright 2024 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.caliper import Caliper


class Saxpy(
    Experiment,
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
            device = "n_ranks"
            self.add_experiment_variable("n_nodes", ["1", "2"], True)
            self.add_experiment_variable("n_ranks", "8")
            self.add_experiment_variable("n_threads_per_proc", ["2", "4"], True)
            self.matrix_experiment_variables(["n", "n_threads_per_proc"])
        else:
            device = "n_gpus"
            n = ["128", "256"] + n
            self.add_experiment_variable("n_gpus", "1", False)
            self.matrix_experiment_variables("n")

        self.add_experiment_variable("n", n, True)

        n_resources = "{" + device + "}"
        self.set_required_variables(
            n_resources=n_resources,
            process_problem_size="{n}/" + n_resources,
            total_problem_size="{n}",
        )

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"saxpy@{app_version}"])
