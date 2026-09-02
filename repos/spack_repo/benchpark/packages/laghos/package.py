# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage


class Laghos(CMakePackage, CudaPackage, ROCmPackage):
    """Laghos (LAGrangian High-Order Solver) is a CEED miniapp that solves the
    time-dependent Euler equations of compressible gas dynamics in a moving
    Lagrangian frame using unstructured high-order finite element spatial
    discretization and explicit high-order time-stepping.
    """

    tags = ["proxy-app", "ecp-proxy-app"]

    homepage = "https://github.com/CEED/Laghos"
    git = "https://github.com/CEED/Laghos.git"

    maintainers("wdhawkins")

    license("BSD-2-Clause")

    version("develop", branch="master")

    variant("metis", default=True, description="Enable/disable METIS support")
    variant("caliper", default=False, description="Enable/disable Caliper support")
    variant("ofast", default=False, description="Enable gcc optimization flags")
    variant("gpu-aware-mpi", default=False, description="Enable GPU aware MPI")
    variant("raja", default=True, description="Use RAJA backend for MFEM")

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    depends_on("mfem+mpi+metis", when="+metis")
    depends_on("mfem+mpi~metis", when="~metis")
    depends_on("mfem+raja", when="+raja")
    depends_on("caliper", when="+caliper")
    depends_on("adiak~shared", when="+caliper")

    depends_on("zlib+optimize+pic~shared")
    depends_on("mfem@develop", when="@develop")
    depends_on("mfem@4.2.0:", when="@3.1")
    depends_on("mfem@4.1.0:4.1", when="@3.0")
    # Recommended mfem version for laghos v2.0 is: ^mfem@3.4.1-laghos-v2.0
    depends_on("mfem@3.4.1-laghos-v2.0", when="@2.0")
    # Recommended mfem version for laghos v1.x is: ^mfem@3.3.1-laghos-v1.0
    depends_on("mfem@3.3.1-laghos-v1.0", when="@1.0,1.1")
    depends_on("mfem+caliper", when="+caliper")
    depends_on("mfem cxxstd=17")

    requires("^[virtuals=zlib-api] zlib")

    depends_on("mpi")
    depends_on("hypre+mpi")
    depends_on("hypre+mixedint~fortran")
    depends_on("hypre+caliper", when="+caliper")

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

    depends_on("hypre+gpu-aware-mpi", when="+gpu-aware-mpi")

    # Replace MPI_Session
    patch(
        "https://github.com/CEED/Laghos/commit/c800883ab2741c8c3b99486e7d8ddd8e53a7cb95.patch?full_index=1",
        sha256="e783a71c3cb36886eb539c0f7ac622883ed5caf7ccae597d545d48eaf051d15d",
        when="@3.1 ^mfem@4.4:",
    )

    def setup_run_environment(self, env):
        if "+gpu-aware-mpi" in self.spec:
            env.set("MFEM_GPU_AWARE_MPI", "1")

    install_time_test_callbacks = []  # type: List[str]

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        build_dir = self.build_directory
        install(join_path(build_dir, "laghos"), prefix.bin)
        install(join_path(build_dir, "sedov"), prefix.bin)

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
            #flags = [
            #    "-x hip",
            #    f"--offload-arch={amdgpu_target}",
            #]
            #args.append(self.define("CMAKE_CXX_FLAGS", " ".join(flags)))
        return args
