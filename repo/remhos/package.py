# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0
from typing import List

from spack.package import *


class Remhos(MakefilePackage, CudaPackage, ROCmPackage):
    """Remhos (REMap High-Order Solver) is a CEED miniapp that performs monotonic
    and conservative high-order discontinuous field interpolation (remap)
    using DG advection-based spatial discretization and explicit high-order
    time-stepping.
    """

    tags = ["proxy-app"]

    homepage = "https://github.com/CEED/Remhos"
    url = "https://github.com/CEED/Remhos/archive/v1.0.tar.gz"
    git = "https://github.com/CEED/Remhos.git"

    maintainers("v-dobrev", "tzanio", "vladotomov")

    license("BSD-2-Clause")

    version("develop", branch="master")
    version("gpu-fom", branch="gpu-fom")
    version("gpu-opt", branch="gpu-opt")
    version("1.0", sha256="e60464a867fe5b1fd694fbb37bb51773723427f071c0ae26852a2804c08bbb32")

    variant("metis", default=True, description="Enable/disable METIS support")
    variant("caliper", default=True, description= "Enable/disable caliper support")

    variant("cuda", default=False, description= "Enable/disable CUDA")
    variant("rocm", default=False, description= "Enable/disable ROCm")

    depends_on("mfem+mpi+metis", when="+metis")
    depends_on("mfem+mpi~metis", when="~metis")
    depends_on("mfem+caliper", when="+caliper")
    depends_on("mfem@develop", when="@develop")
    depends_on("mfem@4.1.0:", when="@1.0")
    depends_on("mfem@develop", when="@gpu-fom")
    depends_on("mfem@4.4_comm_cali", when="@gpu-opt")
    depends_on("mfem cxxstd=14")

    depends_on("mpi")
    depends_on("hypre+mpi")
    #requires("+mpi", when="^hypre+mpi")
    depends_on("hypre+caliper", when="+caliper")
    #depends_on("hypre@2.31.0:")
    depends_on("hypre@2.31.0+mixedint~fortran")


    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")

    depends_on("hypre+cuda+mpi", when="+cuda")
    requires("+cuda", when="^hypre+cuda")
    for arch in ("none", "50", "60", "70", "80"):
        depends_on(f"hypre cuda_arch={arch}", when=f"cuda_arch={arch}")
        depends_on(f"mfem cuda_arch={arch}", when=f"cuda_arch={arch}")
    depends_on("mfem +cuda+mpi", when="+cuda")
    depends_on("mfem +rocm+mpi", when="+rocm")
    depends_on("hypre +rocm +mpi", when="+rocm")
    requires("+rocm", when="^hypre+rocm")
    for target in ("none", "gfx803", "gfx900", "gfx906", "gfx908", "gfx90a", "gfx942"):
        #depends_on(f"hypre amdgpu_target={target}", when=f"amdgpu_target={target}")
        depends_on(f"mfem amdgpu_target={target}", when=f"amdgpu_target={target}")

    @property
    def build_targets(self):
        targets = []
        spec = self.spec
        if "+caliper" in spec:
            cal_dir=spec["caliper"].prefix
            targets.append("CALIPER_DIR=%s" % spec["caliper"].prefix)
            targets.append("ADIAK_DIR=%s" % spec["adiak"].prefix)
        targets.append("MFEM_DIR=%s" % spec["mfem"].prefix)
        targets.append("CONFIG_MK=%s" % spec["mfem"].package.config_mk)
        targets.append("TEST_MK=%s" % spec["mfem"].package.test_mk)

        return targets

    # See lib/spack/spack/build_systems/makefile.py
    def check(self):
        with working_dir(self.build_directory):
            make("tests", *self.build_targets)

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        install("remhos", prefix.bin)
        install_tree("data", prefix.data)
    install_time_test_callbacks: List[str] = []
