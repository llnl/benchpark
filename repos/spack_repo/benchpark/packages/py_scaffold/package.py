# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from spack.package import *
from spack_repo.builtin.build_systems.python import PythonPackage


class PyScaffold(PythonPackage, CudaPackage, ROCmPackage):
    """Scale-Free Fractal benchmark"""

    git = "https://github.com/LBANN/ScaFFold.git"

    version("main", branch="main")

    maintainers("michaelmckinsey")
    license("Apache-2.0")

    variant("mpi", default=True, description="MPI support")
    variant("caliper", default=False, description="Build with Caliper support enabled.")

    # open3d package requires <=3.11
    depends_on("python@3.11", type=("build", "run"))
    # TODO: Get pip._vendor.pyproject_hooks._impl.BackendUnavailable: Cannot import 'setuptools.build_meta' from pip otherwise
    depends_on("py-setuptools", type="build")

    depends_on("mpi")

    depends_on("c", type="build")
    depends_on("cxx", type="build")

    depends_on("caliper+python", when="+caliper", type=("build", "run"))
    depends_on("adiak+python", when="+caliper", type=("build", "run"))

    def cmake_args(self):
        args = super().cmake_args(self)

        args.append(self.define("CMAKE_EXE_LINKER_FLAGS", self.spec['mpi'].libs.ld_flags))
        args.append(self.define("MPI_CXX_LINK_FLAGS", self.spec['mpi'].libs.ld_flags))

        return args

    def setup_build_environment(self, env):
        super().setup_build_environment(env)

        if self.compiler.extra_rpaths:
            for rpath in self.compiler.extra_rpaths:
                env.prepend_path("LD_LIBRARY_PATH", rpath)

        if "+mpi" in self.spec:
            if self.spec["mpi"].extra_attributes:
                if "ldflags" in self.spec["mpi"].extra_attributes:
                    env.append_flags("LDFLAGS", self.spec["mpi"].extra_attributes["ldflags"])
                if "gtl_lib_path" in self.spec["mpi"].extra_attributes:
                    env.prepend_path("LD_LIBRARY_PATH", self.spec['mpi'].extra_attributes["gtl_lib_path"])

    def setup_run_environment(self, env):
        super().setup_run_environment(env)

        if "+mpi" in self.spec:
            if self.spec["mpi"].extra_attributes:
                if "gtl_lib_path" in self.spec["mpi"].extra_attributes:
                    # Avoid gtl error
                    env.prepend_path("LD_LIBRARY_PATH", self.spec['mpi'].extra_attributes["gtl_lib_path"])

        # if self.spec.satisfies("+caliper"):
        #     if self.spec.satisfies("+rocm"):
        #         # Need to set this to libcaliper.so to avoid rocprofiler context error
        #         env.set("ROCP_TOOL_LIBRARIES", os.path.join(self.spec["caliper"].prefix, "lib64", "libcaliper.so"))

        if self.compiler.extra_rpaths:
            for rpath in self.compiler.extra_rpaths:
                env.prepend_path("LD_LIBRARY_PATH", rpath)
