# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import provides


class CudaSystem:
    provides("cuda")

    name = "cuda"

    def verify(self, system):
        assert "cuda" in system.variants
        assert "gtl" in system.variants
        assert hasattr(system, "cuda_arch")
        assert hasattr(system, "cuda_version")
        assert hasattr(system, "gtl_flag")

    def system_specific_variables(self, system):
        return {
            "cuda_arch": system.cuda_arch,
            "cuda_version": system.cuda_version,
            "gtl_flag": system.gtl_flag,
        }
