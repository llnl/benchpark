# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage


class Amg2023(CMakePackage, CudaPackage, ROCmPackage):
    """AMG2023 is a parallel algebraic multigrid solver for linear systems
    arising from problems on unstructured grids. The driver provided here
    builds linear systems for various 3-dimensional problems. It requires
    an installation of hypre-2.31.0 or higher.
    """

    tags = ["benchmark"]
    homepage = "https://github.com/LLNL/AMG2023"
    git = "https://github.com/LLNL/AMG2023.git"

    license("Apache-2.0")

    version("develop", branch="rl_fix2")
    version("20240511", branch="20240511")

    variant("mpi", default=True, description="Enable MPI support")
    variant("openmp", default=False, description="Enable OpenMP support")
    variant("caliper", default=False, description="Enable Caliper monitoring")
    variant("umpire", default=False, description="Enable Umpire support")
    variant("mixedint", default=False, description="Use 64bit integers while reducing memory use")
    variant("gpu-aware-mpi", default=False, description="Enable GPU aware MPI")

    depends_on("c", type="build")
    depends_on("cxx", type="build")

    depends_on("mpi", when="+mpi")
    depends_on("hypre+mpi", when="+mpi")
    requires("+mpi", when="^hypre+mpi")
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")
    depends_on("hypre~caliper")
    depends_on("hypre@:2.29.0", when="@20240511")
    depends_on("hypre@2.30.0:", when="@develop")
    #depends_on("hypre@:2.99")
    depends_on("hypre~fortran")
    depends_on("hypre+mixedint", when="+mixedint")
    depends_on("blas")
    depends_on("lapack")

    depends_on("hip-wrapper", when="+rocm")

    depends_on("hypre+cuda+mpi+umpire", when="+cuda")
    depends_on("hypre~cuda", when="~cuda")

    for sm_ in CudaPackage.cuda_arch_values:
        depends_on("hypre cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))
        depends_on("umpire cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))

    depends_on("hypre+rocm+mpi+umpire", when="+rocm")
    depends_on("hypre~rocm", when="~rocm")
    
    for arch in ROCmPackage.amdgpu_targets:
        depends_on("hypre amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))
        depends_on("umpire amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))

    depends_on("hypre+gpu-aware-mpi", when="+mpi+gpu-aware-mpi")

    def setup_build_environment(self, env):
        if self.spec.satisfies("+cuda"):
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def cmake_args(self):
        cmake_options = []
        cmake_options.append(self.define_from_variant("AMG_WITH_CALIPER", "caliper"))
        cmake_options.append(self.define_from_variant("AMG_WITH_OMP", "openmp"))
        cmake_options.append(self.define_from_variant("AMG_WITH_UMPIRE", "umpire"))
        cmake_options.append(self.define("HYPRE_PREFIX", self.spec["hypre"].prefix))
        if self.spec["hypre"].satisfies("+cuda"):
            cmake_options.append("-DAMG_WITH_CUDA=ON")
        if self.spec["hypre"].satisfies("+rocm"):
            cmake_options.append("-DAMG_WITH_HIP=ON")
        if self.spec["hypre"].satisfies("+mpi"):
            cmake_options.append("-DAMG_WITH_MPI=ON")
        if self.spec.satisfies("+cuda"):
            cmake_options.append(f'-DCMAKE_EXE_LINKER_FLAGS={self.spec["lapack"].libs.ld_flags} {self.spec["blas"].libs.ld_flags}')
        if self.spec.satisfies("+rocm"):
            cmake_options.append(f"-DCMAKE_HIP_COMPILER={self.spec['hip-wrapper'].prefix.bin.hipwrapper}")

        return cmake_options
