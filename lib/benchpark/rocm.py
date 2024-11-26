# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper


class ROCmExperiment:
    variant("rocm", default=False, description="Build and run with ROCm")

    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return "rocm" if self.spec.satisfies("+rocm") else ""

        def get_spack_variants(self):
            return (
                "+rocm amdgpu_target={rocm_arch}"
                if self.spec.satisfies("+rocm")
                else "~rocm"
            )
