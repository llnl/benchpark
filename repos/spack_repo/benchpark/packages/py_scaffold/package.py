# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.py_scaffold.package import (
    PyScaffold as BuiltinPyScaffold,
)


class PyScaffold(BuiltinPyScaffold):
    """Scale-Free Fractal benchmark"""

    def setup_build_environment(self, env):
        super().setup_build_environment(env)

        for rpath in self.compiler.extra_rpaths:
            env.prepend_path("LD_LIBRARY_PATH", rpath)

        if self.spec.satisfies("+mpi"):
            mpi_attrs = self.spec["mpi"].extra_attributes
            if "ldflags" in mpi_attrs:
                env.append_flags("LDFLAGS", mpi_attrs["ldflags"])
            if "gtl_lib_path" in mpi_attrs:
                env.prepend_path("LD_LIBRARY_PATH", mpi_attrs["gtl_lib_path"])

    def setup_run_environment(self, env):
        super().setup_run_environment(env)

        if self.spec.satisfies("+mpi"):
            mpi_attrs = self.spec["mpi"].extra_attributes
            if "gtl_lib_path" in mpi_attrs:
                # Avoid gtl error
                env.prepend_path("LD_LIBRARY_PATH", mpi_attrs["gtl_lib_path"])

        for rpath in self.compiler.extra_rpaths:
            env.prepend_path("LD_LIBRARY_PATH", rpath)
