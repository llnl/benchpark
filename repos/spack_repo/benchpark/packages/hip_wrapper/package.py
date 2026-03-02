# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import os.path
import stat

from spack.package import *
from spack.package import LinkTree
from spack_repo.builtin.build_systems.bundle import BundlePackage
from spack_repo.builtin.packages.mpich.package import MpichEnvironmentModifications


class HipWrapper(BundlePackage):

    version("1.0.0")

    depends_on("llvm-amdgpu")

    def install(self, spec, prefix):
        mkdir(self.prefix.bin)
        fpath = os.path.join(self.prefix.bin, "hipwrapper")
        hip_compiler = os.path.join(spec["llvm-amdgpu"].prefix.llvm.bin, "clang++")
        # Usually spack sets CXX to be the spack compiler wrapper
        with open(fpath, "w") as f:
            f.write(
                f"""\
#!/bin/bash

SPACK_CXX={hip_compiler} $CXX "$@"
"""
                    )
        st = os.stat(fpath)
        os.chmod(fpath, st.st_mode | stat.S_IEXEC)
