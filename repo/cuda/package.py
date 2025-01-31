# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from spack.package import *
import spack.pkg.builtin.cuda


class Cuda(spack.pkg.builtin.cuda.Cuda):
    # Layout of hpc-sdk puts some headers in sibling directories:
    # cuda compiler in /opt/nvidia/hpc_sdk/Linux_aarch64/24.7/cuda/12.5
    # cufft in         /opt/nvidia/hpc_sdk/Linux_aarch64/24.7/math_libs/12.5
    variant("im-hpc-sdk", default=False)

    @property
    def headers(self):
        home = getattr(spec.package, "home")
        headers = fs.find_headers("*", root=home.include, recursive=True)

        if self.spec.satisfies("+im-hpc-sdk"):
            prefix = pathlib.Path(self.prefix)
            version_component = prefix.parent.name  # 12.5
            split_point = prefix.parent.parent
            cufft_base = split_point / "math_libs" / version_component
            headers = headers + fs.find_headers("cufft.h", root=str(cufft_base), recursive=True)    
            
        return headers
