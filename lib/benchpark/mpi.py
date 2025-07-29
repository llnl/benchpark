# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import requires, variant
from benchpark.experiment import ExperimentHelper


class MpiOnlyExperiment:
    requires("mpi")
    variant("mpi", default=True, description="Run with MPI only")

    def __init__(self):
        super().__init__()
        if self.spec.variants["mpi"][0]:
            self.device_type = "cpu"
        self.programming_models.append("mpi")

    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return "mpi" if self.spec.satisfies("+mpi") else ""
