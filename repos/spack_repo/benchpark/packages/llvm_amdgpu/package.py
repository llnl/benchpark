# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import spack_repo.builtin.packages.llvm_amdgpu.package
from spack.package import *


class LlvmAmdgpu(spack_repo.builtin.packages.llvm_amdgpu.package.LlvmAmdgpu):
    provides("fortran") 

