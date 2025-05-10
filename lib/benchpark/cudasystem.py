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

    def cuda_arch(self):
        return NotImplementedError("Each system must implement cuda_arch")

    def default_cuda_version(self):
        return NotImplementedError("Each system must implement cuda_version")
