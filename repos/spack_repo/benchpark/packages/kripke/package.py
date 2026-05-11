# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage


class Kripke(CMakePackage, CudaPackage, ROCmPackage):
    """Kripke is a simple, scalable, 3D Sn deterministic particle
    transport proxy/mini app.
    """

    homepage = "https://computing.llnl.gov/projects/co-design/kripke"
    git = "https://github.com/LLNL/Kripke.git"

    tags = ["proxy-app"]

    maintainers("vsrana01")

    license("BSD-3-Clause")

    version("develop", branch="develop", submodules=False)
    version("2025.12.0", submodules=False, commit="01f6f85c02ceffcd2bc06e42cee997867dd142c5")
    version("2025.07.0", submodules=False, commit="8cf38433a6a11e0dcd17864e649b2d045159ee9c")
    version(
        "1.2.7.0", submodules=False, commit="db920c1f5e1dcbb9e949d120e7d86efcdb777635"
    )
    version(
        "1.2.4", submodules=False, tag="v1.2.4", commit="d85c6bc462f17a2382b11ba363059febc487f771"
    )
    version(
        "1.2.3", submodules=True, tag="v1.2.3", commit="66046d8cd51f5bcf8666fd8c810322e253c4ce0e"
    )
    version(
        "1.2.2",
        submodules=True,
        tag="v1.2.2-CORAL2",
        commit="a12bce71e751f8f999009aa2fd0839b908b118a4",
    )
    version(
        "1.2.1",
        submodules=True,
        tag="v1.2.1-CORAL2",
        commit="c36453301ddd684118bb0fb426cfa62764d42398",
    )
    version(
        "1.2.0",
        submodules=True,
        tag="v1.2.0-CORAL2",
        commit="67e4b0a2f092009d61f44b5122111d388a3bec2a",
    )

    variant("mpi", default=True, description="Build with MPI.")
    variant("openmp", default=False, description="Build with OpenMP enabled.")
    variant("caliper", default=False, description="Build with Caliper support enabled.")
    variant("single_memory", default=False, description="Enable single memory space model in rocm")

    conflicts("+single_memory", when="~rocm")
    depends_on("chai+single_memory", when="+single_memory")

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    depends_on("chai@2025.12.0+raja", when="@develop")
    depends_on("chai@2025.12.0+raja", when="@2025.12.0")
    depends_on("fmt@9.1", when=f"^chai@2024.07.0")
    depends_on("chai@2024.07.0+raja", when="@:2025.07.0")
    depends_on("chai@2024.07.0+raja", when="@1.2.7.0:2025.07.0")
    depends_on("fmt@9.1", when=f"^chai@2024.07.0")

    depends_on("mpi", when="+mpi")
    depends_on("chai+mpi", when="+mpi")
    depends_on("caliper", when="+caliper")
    depends_on("adiak@0.4:", when="+caliper")
    conflicts("^blt@:0.3.6", when="+rocm")
    conflicts("^blt@0.7:", when="^chai@:2024.07.0")

    depends_on("blt@0.6.2:", type="build", when=f"@1.2.7:")

    depends_on("chai+openmp", when="+openmp")
    depends_on("chai~openmp", when="~openmp")

    depends_on("chai+cuda", when="+cuda")
    depends_on("chai~cuda", when="~cuda")
    for sm_ in CudaPackage.cuda_arch_values:
        depends_on("chai cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))

    depends_on("chai+rocm", when="+rocm")
    depends_on("chai~rocm", when="~rocm")
    for arch in ROCmPackage.amdgpu_targets:
        depends_on("chai amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))

    depends_on("umpire+openmp", when="+openmp")
    depends_on("umpire~openmp", when="~openmp")
    
    depends_on("umpire+cuda", when="+cuda")
    depends_on("umpire~cuda", when="~cuda")
    for sm_ in CudaPackage.cuda_arch_values:
        depends_on("umpire cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))

    depends_on("umpire+rocm", when="+rocm")
    depends_on("umpire~rocm", when="~rocm")
    for arch in ROCmPackage.amdgpu_targets:
        depends_on("umpire amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))

    def setup_build_environment(self, env):
        spec = self.spec
        if "+cuda" in spec:
            env.set("CUDAHOSTCXX", self.spec["mpi"].mpicxx)
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
      super().setup_run_environment(env)

      if self.compiler.extra_rpaths:
        for rpath in self.compiler.extra_rpaths:
          env.prepend_path("LD_LIBRARY_PATH", rpath)

    def cmake_args(self):
        spec = self.spec
        args = []

        if "+rocm" in spec or "+cuda" in spec:
            enable_chai = "ON"
            enable_chai_single_memory = "ON" if "+single_memory" in spec else "OFF"
        else:
            enable_chai = "OFF"
            enable_chai_single_memory = "OFF"

        args.extend(
            [
                "-DCAMP_DIR=%s" % self.spec["camp"].prefix,
                "-DBLT_SOURCE_DIR=%s" % self.spec["blt"].prefix,
                "-Dumpire_DIR=%s" % self.spec["umpire"].prefix,
                "-DRAJA_DIR=%s" % self.spec["raja"].prefix,
                "-Dchai_DIR=%s" % self.spec["chai"].prefix,
                "-DENABLE_CHAI=%s" % enable_chai,
                "-DENABLE_CHAI_SINGLE_MEMORY=%s" % enable_chai_single_memory,
                "-DMPI_CXX_LINK_FLAGS='%s'" % self.spec['mpi'].libs.ld_flags,
            ]
        )

        if "+openmp" in spec:
            args.append("-DENABLE_OPENMP=ON")

        if "+caliper" in spec:
            args.append("-DENABLE_CALIPER=ON")

        if "+mpi" in spec:
            args.append("-DENABLE_MPI=ON")
            args.append(self.define("CMAKE_CXX_COMPILER", self.spec["mpi"].mpicxx))

        if "+rocm" in spec:
            # Set up the hip macros needed by the build
            args.append("-DENABLE_HIP=ON")
            args.append("-DHIP_ROOT_DIR={0}".format(spec["hip"].prefix))
            rocm_archs = spec.variants["amdgpu_target"].value
            if "none" not in rocm_archs:
                arch_str = ",".join(rocm_archs)
                args.append("-DHIP_HIPCC_FLAGS=--amdgpu-target={0}".format(arch_str))
                args.append("-DCMAKE_HIP_ARCHITECTURES={0}".format(arch_str))
        else:
            # Ensure build with hip is disabled
            args.append("-DENABLE_HIP=OFF")

        if "+cuda" in spec:
            args.append("-DENABLE_CUDA=ON")
            args.append(self.define("CMAKE_CUDA_HOST_COMPILER", self.spec["mpi"].mpicxx))
            if not spec.satisfies("cuda_arch=none"):
                cuda_arch = spec.variants["cuda_arch"].value
                args.append("-DCUDA_ARCH={0}".format(cuda_arch[0]))
                args.append("-DCMAKE_CUDA_ARCHITECTURES={0}".format(cuda_arch[0]))
            args.append(
                "-DCMAKE_CUDA_FLAGS=--extended-lambda -I=%s"
                % (self.spec["mpi"].prefix.include)
            )
        else:
            args.append("-DENABLE_CUDA=OFF")

        return args

    def install(self, spec, prefix):
        # Kripke does not provide install target, so we have to copy
        # things into place.
        mkdirp(prefix.bin)
        install(join_path(self.build_directory, "kripke.exe"), prefix.bin)
