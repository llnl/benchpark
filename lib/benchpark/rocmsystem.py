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

    # Specify default rocm_arch and default_rocm_version
    # How to make sure the derived classes overwrite this?
    def system_specific_variables(self):
        return {
            "rocm_arch": "gfx90a",
            "default_rocm_version": self.spec.variants["rocm"][0].replace("-", "."),
        }
