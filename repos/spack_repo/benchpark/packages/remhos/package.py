# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *
from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage


class Remhos(CMakePackage, CudaPackage, ROCmPackage):
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

    patch("remhos-cmake.patch")

    version("develop", branch="master")
    version("2.0", branch="master")
    version("1.0", sha256="e60464a867fe5b1fd694fbb37bb51773723427f071c0ae26852a2804c08bbb32")

    variant("metis", default=True, description="Enable/disable METIS support")
    variant("caliper", default=False, description="Enable/disable Caliper support")
    variant("gpu-aware-mpi", default=False, description="Enable GPU aware MPI")
    variant("raja", default=True, description="Use RAJA backend for MFEM")

    depends_on("cxx", type="build")
    depends_on("c", type="build")
    depends_on("hip-lang", type="build")

    depends_on("mpi")

    depends_on("camp@2026.07.1:", when="@develop")
    depends_on("umpire@2026.07.1:", when="@develop")
    depends_on("raja@2026.07.0: ~examples~exercises cxxstd=20", when="@develop")

    depends_on("camp@2026.07.1", when="@2.0")
    depends_on("umpire@2026.07.1", when="@2.0")
    depends_on("raja@2026.07.0 ~examples~exercises cxxstd=20", when="@2.0")

    depends_on("mfem+mpi+metis", when="+metis")
    depends_on("mfem+mpi~metis", when="~metis")
    depends_on("mfem+raja", when="+raja")

    depends_on("mfem@develop", when="@develop")
    depends_on("mfem@4.10", when="@2.0")
    depends_on("mfem@4.1.0:", when="@1.0")
    depends_on("mfem+caliper", when="+caliper")
    depends_on("mfem cxxstd=20", when="@develop")
    depends_on("mfem cxxstd=20", when="@2.0")

    depends_on("caliper", when="+caliper")
    depends_on("adiak~shared", when="+caliper")

    depends_on("zlib+optimize+pic~shared")
    requires("^[virtuals=zlib-api] zlib")

    depends_on("hypre+mpi")
    depends_on("hypre+mixedint~fortran")
    depends_on("hypre+caliper", when="+caliper")

    depends_on("hypre~cuda", when="~cuda")
    depends_on("mfem~cuda", when="~cuda")

    with when("+cuda"):
        depends_on("hypre+cuda+umpire")
        depends_on("mfem+cuda+umpire")
        for sm_ in CudaPackage.cuda_arch_values:
            depends_on("hypre cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))
            depends_on("mfem cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))
            depends_on("umpire cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))

    depends_on("hypre~rocm", when="~rocm")
    depends_on("mfem~rocm", when="~rocm")
    
    with when("+rocm"):
        depends_on("hypre+rocm+umpire")
        depends_on("mfem+rocm+umpire")
        for arch in ROCmPackage.amdgpu_targets:
            depends_on("hypre amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))
            depends_on("mfem amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))
            depends_on("umpire amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))

    depends_on("hypre+gpu-aware-mpi", when="+gpu-aware-mpi")

    def setup_run_environment(self, env):
        if "+gpu-aware-mpi" in self.spec:
            env.set("MFEM_GPU_AWARE_MPI", "1")

    install_time_test_callbacks = []  # type: List[str]

    def cmake_args(self):
        spec = self.spec
        args = []
        args.append(f"-DMFEM_DIR={spec['mfem'].prefix}")
        if self.spec.satisfies("+rocm"):
            args.append("-DMFEM_USE_HIP=ON")
            args.append(f"-DCMAKE_HIP_COMPILER={env['HIPCXX']}")
            args.append(f"-DCMAKE_CXX_COMPILER={env['HIPCXX']}")
            amdgpu_target = ";".join(spec.variants["amdgpu_target"].value)
            args.append(self.define("CMAKE_HIP_ARCHITECTURES", amdgpu_target))
        if self.spec.satisfies("^mfem cxxstd=20"):
            args.append("-DCMAKE_CXX_STANDARD=20")
        if self.spec.satisfies("+caliper"):
            args.append("-DREMHOS_USE_CALIPER=ON")
        return args

    def install(self, spec, prefix):
        super().install(spec, prefix)
        install(self.prefix.bin.remhos_main, self.prefix.bin.remhos)
