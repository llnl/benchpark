# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.camp.package import Camp as BuiltinCamp


class Camp(BuiltinCamp):

    variant("default_stream", default=False, description="Use default stream")

    def cmake_args(self):
        options = super().cmake_args()
        options.append(self.define_from_variant("CAMP_USE_PLATFORM_DEFAULT_STREAM", "default_stream"))

        return options
