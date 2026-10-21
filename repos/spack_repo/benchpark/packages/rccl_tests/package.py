# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import conflicts
from spack_repo.builtin.build_systems.rocm import ROCmPackage
from spack_repo.builtin.packages.rccl_tests.package import RcclTests as BuiltinRcclTests


class RcclTests(BuiltinRcclTests, ROCmPackage):
    """Expose the standard ROCm variants expected by Benchpark."""

    conflicts("~rocm", msg="rccl-tests requires ROCm")

    def cmake_args(self):
        args = super().cmake_args()
        targets = self.spec.variants["amdgpu_target"].value
        if targets:
            args.append(self.define("GPU_TARGETS", ";".join(targets)))
        return args
