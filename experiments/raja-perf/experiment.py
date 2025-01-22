# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
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
    Caliper,
):
    variant(
        "workload",
        default="suite",
        description="base Rajaperf suite or other problem",
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
                n_resources = pv

        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(n_resources.keys()): list(n_resources.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            n_resources = scaled_variables["n_ranks"]

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", n_resources, True)
        elif self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_ranks", n_resources, True)
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        else:
            self.add_experiment_variable("n_ranks", n_resources, True)

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"

        if self.spec.satisfies("+cuda"):
            system_specs["cuda_version"] = "{default_cuda_version}"
            system_specs["cuda_arch"] = "{cuda_arch}"
        if self.spec.satisfies("+rocm"):
            system_specs["rocm_arch"] = "{rocm_arch}"

        self.add_spack_spec(system_specs["mpi"])

        self.add_spack_spec(
            self.name, [f"raja-perf@{app_version}", system_specs["compiler"]]
        )
