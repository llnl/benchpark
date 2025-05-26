# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import requires, variant
from benchpark.experiment import ExperimentHelper


class CudaExperiment:
    requires("cuda")
    variant("cuda", default=False, description="Build and run with CUDA")

    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return "cuda" if self.spec.satisfies("+cuda") else ""

        def get_spack_variants(self):
            return (
                "+cuda cuda_arch={cuda_arch}"
                if self.spec.satisfies("+cuda")
                else "~cuda"
            )
