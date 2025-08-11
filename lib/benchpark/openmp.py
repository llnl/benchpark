# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import requires, variant
from benchpark.experiment import ExperimentHelper


class OpenMPExperiment:
    requires("openmp", when="+openmp")
    variant("openmp", default=False, description="Build and run with OpenMP")

    def __init__(self):
        super().__init__()
        if self.spec.variants["openmp"][0]:
            self.device_type = "cpu"
        self.programming_models.append("openmp")

    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return "openmp" if self.spec.satisfies("+openmp") else ""

        def get_spack_variants(self):
            return "+openmp" if self.spec.satisfies("+openmp") else "~openmp"
