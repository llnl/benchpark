# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import provides, variant


class ROCmSystem:
    provides("rocm")

    def verify(self, system):
        assert "rocm" in system.variants
        assert hasattr(system, "rocm_arch")
        assert hasattr(system, "default_rocm_version")

    def system_attrs(self):
        return ["rocm_arch","default_rocm_version"]
