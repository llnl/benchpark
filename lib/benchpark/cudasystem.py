# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import provides, variant


class CudaSystem:
    provides("cuda")

    # How can we enforce that all CudaSystems expose a cuda variant?
    variant(
        "cuda",
        default="11-8-0",
        values=("11-8-0", "10-1-243"),
        description="CUDA version",
    )

    # Specify default cuda_arch and default_cuda_version
    # How to make sure the derived classes overwrite this?
    def system_specific_variables(self):
        return {
            "cuda_arch": 70,
            "default_cuda_version": self.spec.variants["cuda"][0].replace("-", "."),
        }
