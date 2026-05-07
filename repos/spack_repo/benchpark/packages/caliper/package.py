# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.caliper.package import Caliper as BuiltinCaliper


class Caliper(BuiltinCaliper):
    """Caliper is a program instrumentation and performance measurement
    framework. It is designed as a performance analysis toolbox in a
    library, allowing one to bake performance analysis capabilities
    directly into applications and activate them at runtime.
    """

    def setup_build_environment(self, env):
        # Do not insert -lmpi_gtl_hsa, this seems to cause a hang when doing
        # rocm profiling in caliper
        env.set("SPACK_GTL", "diverted")

    # rocp_sdk broken in upstream papi package for any ver less than 7.2
    depends_on("papi@7.2:+topdown", when="+papi")
