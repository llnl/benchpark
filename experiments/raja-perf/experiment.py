# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.caliper import Caliper


class RajaPerf(
    Experiment,
    StrongScaling,
    CudaExperiment,
    ROCmExperiment,
    OpenMPExperiment,
    Caliper,
):

    maintainers("michaelmckinsey1")

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

    variant(
        "total_size",
        default=1048576,
        description="total problem size (will be divided by ranks)",
    )

    variant(
        "repfact",
        default=1,
        description="Multiplier on number of repitions to run each kernel",
    )

    # variant(
    #     "variants",
    #     default="None",
    # )

    # variant(
    #     "tunings",
    #     default="None",
    # )

    def compute_applications_section(self):

        n_resources = {"n_ranks": 1}
        total_size = int(self.spec.variants["total_size"][0])
        execute = "raja-perf.exe"

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

        if isinstance(n_resources, list):
            size = [int(total_size / res) for res in n_resources]
        else:
            size = total_size
        self.add_experiment_variable("size", size, True)

        self.add_experiment_variable("repfact", self.spec.variants["repfact"][0], True)

        # rajaperf_variants = self.spec.variants["variants"][0].replace("-", " ")
        # rajaperf_tunings = self.spec.variants["tunings"][0].replace("-", " ")
        # if rajaperf_variants != "None":
        #     execute += " --variants " + rajaperf_variants
        # if rajaperf_tunings != "None":
        #     execute += " --tunings " + rajaperf_tunings

        self.add_experiment_variable("execute", execute, True)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"raja-perf@{app_version}"])
