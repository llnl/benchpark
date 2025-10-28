# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.cuda import CudaExperiment
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.rocm import ROCmExperiment


class Commbench(
    Experiment,
    CudaExperiment,
    ROCmExperiment,
):
    variant("workload", description="workload name", default="basic")
    maintainers("arhag23")

    def compute_applications_section(self):
        self.add_experiment_variable("n_ranks", 2, True)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            lib = "mpi"
        else:
            lib = "mpi"

        input_variables = {
            "size": "100000000",
            "lib": f"{lib}",
            "pattern": "broadcast",
        }

        for k, v in input_variables.items():
            self.add_experiment_variable(k, v, True)

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{size}",
            total_problem_size="{size}*{n_ranks}",
        )

    def compute_package_section(self):
        spack_specs = []
        spack_specs = " ".join(spack_specs)
        self.add_package_spec(self.name, [f"commbench {spack_specs}"])
