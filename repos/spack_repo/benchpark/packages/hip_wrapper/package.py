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

    def setup_dependent_build_environment(self, env, dependent_spec):
        rpaths = []
        if dependent_spec.package.compiler.extra_rpaths:
            for rpath in dependent_spec.package.compiler.extra_rpaths:
                rpaths.append(f"-Wl,-rpath,{rpath}")
        env.set("SPACK_HIP_WRAPPER_LIBS", " ".join(rpaths))

    def dependent_cmake_args(self, dependent_spec: Spec) -> List[str]:
        x = self.spec.prefix.bin.hipwrapper
        return [f"-DCMAKE_HIP_COMPILER_LAUNCHER={x}"]

    def install(self, spec, prefix):
        mkdir(self.prefix.bin)
        fpath = os.path.join(self.prefix.bin, "hipwrapper")
        with open(fpath, "w") as f:
            f.write(
                f"""\
#!/bin/bash

compiler="$1"
shift

is_compile=0
for arg in "$@"; do
    if [[ "$arg" == "-c" ]]; then
        is_compile=1
        break
    fi
done

if [[ $is_compile -eq 1 ]]; then
    exec "$compiler" "$@"
else
    exec "$compiler" $SPACK_HIP_WRAPPER_LIBS "$@"
fi
"""
                    )
        st = os.stat(fpath)
        os.chmod(fpath, st.st_mode | stat.S_IEXEC)
