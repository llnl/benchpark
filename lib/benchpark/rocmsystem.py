# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import provides, variant


class ROCmSystem:
    provides("rocm")

    # How can we enforce that all ROCmSystems expose a rocm variant?
    variant(
        "rocm",
        default="6.2.4",
        values=("5.7.1", "6.2.4", "6.3.1"),
        description="ROCm version",
    )

    def set_rocm_arch(self):
        return NotImplementedError("Each system must implement set_rocm_arch")

    def set_default_rocm_version(self):
        return NotImplementedError("Each system must implement set_rocm_version")
    
