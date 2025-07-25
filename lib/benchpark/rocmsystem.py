# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import provides


class ROCmSystem:
    provides("rocm")

    name = "rocm"

    def verify(self, system):
        assert "rocm" in system.variants
        assert "gtl" in system.variants
        assert hasattr(system, "rocm_arch")
        assert hasattr(system, "rocm_version")
        assert hasattr(system, "gtl_flag")

    def system_specific_variables(self, system):
        return {
            "rocm_arch": system.rocm_arch,
            "rocm_version": system.rocm_version,
            "gtl_flag": system.gtl_flag,
        }
