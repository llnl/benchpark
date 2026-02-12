# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.makefile import MakefilePackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage


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
    variant("caliper", default=False, description="Enable/disable Caliper support")

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    depends_on("mfem+mpi+metis", when="+metis")
    depends_on("mfem+mpi~metis", when="~metis")
    depends_on("caliper", when="+caliper")
    depends_on("adiak~shared", when="+caliper")

    depends_on("zlib+optimize+pic~shared")
    depends_on("mfem@develop", when="@develop")
    depends_on("mfem@4.1.0:", when="@1.0")
    depends_on("mfem@develop", when="@gpu-fom")
    depends_on("mfem@develop", when="@gpu-opt")
    depends_on("mfem+caliper", when="+caliper")
    depends_on("mfem cxxstd=17")

    requires("^[virtuals=zlib-api] zlib")
    depends_on("hypre+cuda+mpi+umpire", when="+cuda")
    depends_on("hypre~cuda", when="~cuda")
    depends_on("mfem+cuda+mpi+umpire", when="+cuda")
    depends_on("mfem~cuda", when="~cuda")

    for sm_ in CudaPackage.cuda_arch_values:
        depends_on("hypre cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))
        depends_on("mfem cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))
        depends_on("umpire cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))

    depends_on("hypre+rocm+mpi+umpire", when="+rocm")
    depends_on("hypre~rocm", when="~rocm")
    depends_on("mfem+rocm+mpi+umpire", when="+rocm")
    depends_on("mfem~rocm", when="~rocm")
    
    for arch in ROCmPackage.amdgpu_targets:
        depends_on("hypre amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))
        depends_on("mfem amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))
        depends_on("umpire amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))

    depends_on("hypre+gpu-aware-mpi", when="^cray-mpich+gtl")

    def setup_build_environment(self, env):
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    @property
    def build_targets(self):
        targets = []
        spec = self.spec

        targets.append("MFEM_DIR=%s" % spec["mfem"].prefix)
        targets.append("CONFIG_MK=%s" % spec["mfem"].package.config_mk)
        targets.append("TEST_MK=%s" % spec["mfem"].package.test_mk)
        if "+caliper" in self.spec:
            targets.append("CALIPER_DIR=%s" % spec["caliper"].prefix)
            targets.append("ADIAK_DIR=%s" % spec["adiak"].prefix)
        return targets

    # See lib/spack/spack/build_systems/makefile.py
    def check(self):
        with working_dir(self.build_directory):
            make("test", *self.build_targets)

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        install("remhos", prefix.bin)
        install_tree("data", prefix.data)
