# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
from benchpark.scaling import WeakScaling
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.expr.builtin.caliper import Caliper

class RajaPerf(
    Experiment,
    StrongScaling,
    CudaExperiment,
    ROCmExperiment,
    OpenMPExperiment,
):
    variant(
        "workload",
        default="suite",
        description="base Rajaperf suiteor other problem",
    )

    variant(
        "version",
        default="develop",
        description="app version",
    )

    def compute_applications_section(self):

        n_resources = {"n_ranks": 1}
        
        if self.spec.satisfies("+single_node"):
            for pk, pv in n_resources.items():
                self.add_experiment_variable(pk, pv, True)
        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(n_resources.keys()): list(n_resources.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)
            # 256 mb
            self.add_experiment_variable("b", "268435456 / {n_nodes}", True)

        self.add_experiment_variable("t", t, True)
        self.add_experiment_variable(
            "n_ranks", "{sys_cores_per_node} * {n_nodes}", True
        )

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"

        # set package spack specs
        self.add_spack_spec(system_specs["mpi"])

        self.add_spack_spec(self.name, [f"raja-perf@{app_version}", system_specs["compiler"]])
