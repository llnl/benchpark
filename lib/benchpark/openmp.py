# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper


class OpenMPExperiment:
    variant("openmp", default=False, description="Build and run with OpenMP")

    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return "openmp" if self.spec.satisfies("+openmp") else ""

        def get_spack_variants(self):
            return "+openmp" if self.spec.satisfies("+openmp") else "~openmp"
