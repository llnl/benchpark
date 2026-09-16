# Copyright 2026 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType


class HecbenchSoftmax(
    Experiment,
    ProgrammingModel(ProgrammingModelType.Cuda, ProgrammingModelType.Rocm),
):
    variant(
        "workload",
        default="softmax",
        values=("softmax",),
        description="HeCBench Softmax workload",
    )
    variant(
        "version",
        default="2026-08-13",
        values=("2026-08-13",),
        description="Pinned HeCBench source version",
    )
    variant(
        "implementation",
        default="1",
        values=("0", "1"),
        description="Softmax implementation selector",
    )

    maintainers("chung38")

    def __init__(self, spec):
        super().__init__(spec)
        self.name = "hecbench-softmax"

    def compute_applications_section(self):
        model = "hip" if self.spec.satisfies("+rocm") else "cuda"
        if self.spec.satisfies("exec_mode=test"):
            num_slices, slice_size, internal_repetitions = 8, 128, 2
        else:
            num_slices, slice_size, internal_repetitions = 8192, 1024, 50

        self.add_experiment_variable("model", model, True)
        self.add_experiment_variable("num_slices", num_slices, True)
        self.add_experiment_variable("slice_size", slice_size, True)
        self.add_experiment_variable(
            "implementation", self.spec.variants["implementation"][0], True
        )
        self.add_experiment_variable(
            "internal_repetitions", internal_repetitions, True
        )
        self.add_experiment_variable("n_nodes", 1, False)
        self.add_experiment_variable("n_ranks", 1, False)
        self.add_experiment_variable("n_gpus", 1, False)
        self.set_required_variables(
            n_resources="1",
            process_problem_size="{num_slices}*{slice_size}",
            total_problem_size="{num_slices}*{slice_size}",
        )

    def compute_package_section(self):
        self.add_package_spec(
            self.name,
            [
                f"hecbench{self.determine_version()} "
                "benchmark=softmax ~caliper "
            ],
        )
