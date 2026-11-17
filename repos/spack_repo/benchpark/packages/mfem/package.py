# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from spack_repo.builtin.packages.mfem.package import Mfem as BuiltinMfem
from spack.package import *

class Mfem(BuiltinMfem):
    requires("cxxstd=20", when="^raja cxxstd=20")

    def get_make_config_options(self, spec, prefix):
        """Override to use Spack's HIP compiler wrapper instead of raw hipcc.

        This ensures that downstream makefile-based applications (laghos, remhos)
        that inherit MFEM_CXX from config.mk will use the Spack wrapper, which
        properly handles transitive dependencies and compiler runtime libraries.
        """
        # Get the base options from parent class
        options = super().get_make_config_options(spec, prefix)

        # If this is a ROCm build, replace HIP_CXX with the Spack wrapper
        if "+rocm" in spec:
            # Find and replace the HIP_CXX option
            new_options = []
            for opt in options:
                if opt.startswith("HIP_CXX="):
                    # Replace with Spack's HIPCXX wrapper from environment
                    # Falls back to raw hipcc if HIPCXX not set
                    hipcxx = os.environ.get('HIPCXX', spec["hip"].hipcc)
                    new_options.append(f"HIP_CXX={hipcxx}")
                else:
                    new_options.append(opt)
            return new_options

        return options

