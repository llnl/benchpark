# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment


class Genesis(Experiment, MpiOnlyExperiment, OpenMPExperiment):

    variant(
        "workload",
        default="DHFR",
        values=("DHFR", "ApoA1", "UUN", "cryoEM"),
        description="genesis",
    )

    variant(
        "version",
        default="2.1.6",
        values=("2.1.6", "main"),
        description="app version",
    )

    maintainers("jdomke", "SBA0486")

    def compute_applications_section(self):
        if self.spec.satisfies("exec_mode=test"):
            self.add_experiment_variable("n_nodes", ["1"], True)
        # Must be exec_mode=perf
        else:
            self.add_experiment_variable("n_nodes", ["2"], True)

        self.add_experiment_variable("experiment_setup", "")
        self.add_experiment_variable("lx", "32")
        self.add_experiment_variable("ly", "6")
        self.add_experiment_variable("lz", "4")
        self.add_experiment_variable("lt", "3")
        self.add_experiment_variable("px", "1")
        self.add_experiment_variable("py", "1")
        self.add_experiment_variable("pz", "1")
        self.add_experiment_variable("pt", "1")
        self.add_experiment_variable("tol_outer", "-1")
        self.add_experiment_variable("tol_inner", "-1")
        self.add_experiment_variable("maxiter_plus1_outer", "6")
        self.add_experiment_variable("maxiter_inner", "50")

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("processes_per_node", ["8"])
            self.add_experiment_variable("n_ranks", "{processes_per_node} * {n_nodes}")
            self.add_experiment_variable("omp_num_threads", ["12"])
            self.add_experiment_variable("arch", "OpenMP")

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{lx}*{ly}*{lz}/{n_ranks}",
            total_problem_size="{lx}*{ly}*{lz}",
        )

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"genesis{self.determine_version()}"])
