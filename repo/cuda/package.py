# Copyright 2024 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

import llnl.util.tty as tty
import spack_repo.builtin.packages.cuda.package
from llnl.util.filesystem import find_headers
from spack.package import *


class Cuda(spack_repo.builtin.packages.cuda.package.Cuda):
    # Layout of hpc-sdk puts some headers in sibling directories:
    # cuda compiler in /opt/nvidia/hpc_sdk/Linux_aarch64/24.7/cuda/12.5
    # cufft in         /opt/nvidia/hpc_sdk/Linux_aarch64/24.7/math_libs/12.5
    # In this case, we assume that the external prefix is set to the first path
    variant("im-hpc-sdk", default=False)

    @property
    def headers(self):
        home = getattr(self.spec.package, "home")
        headers = find_headers("*", root=home.include, recursive=True)

        if self.spec.satisfies("+im-hpc-sdk"):
            prefix = pathlib.Path(self.prefix)
            version_component = prefix.name  # 12.5
            split_point = prefix.parent.parent
            cufft_base = split_point / "math_libs" / version_component
            #tty.debug(f"<---- {prefix}\n\t{split_point}\n\t{cufft_base}")
            headers = headers + find_headers("cufft", root=str(cufft_base), recursive=True)

        return headers
