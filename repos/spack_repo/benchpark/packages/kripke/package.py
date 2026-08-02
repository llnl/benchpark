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

    version("develop", branch="llnl/bugfix/chen59/devicedirectsegfault", submodules=False)
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
    variant("chai", default=True, description="Build with CHAI/Umpire.")
    variant("openmp", default=False, description="Build with OpenMP enabled.")
    variant("caliper", default=False, description="Build with Caliper support enabled.")
    variant("gpu-aware-mpi", default=False, description="Enable GPU-aware MPI")

    variant(
        "cxxstd",
        default="17",
        values=("11", "14", "17", "20"),
        description="C++ standard to build with",
    )

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    # camp_version = "main"
    camp_version = "2025.12.0"
    # chai_version = "develop"
    chai_version = "2025.12.0"
    # raja_version = "develop"
    raja_version = "2025.12.0"
    # umpire_version = "develop"
    umpire_version = "2025.12.0"

    with when("cxxstd=11"):
      cxxstd = "11"
    with when("cxxstd=14"):
      cxxstd = "14"
    with when("cxxstd=17"):
      cxxstd = "17"
    with when("cxxstd=20"):
      cxxstd = "20"
 
    depends_on(f"camp@{camp_version}", when="@develop")
    depends_on(f"raja@{raja_version}~examples~exercises cxxstd={cxxstd}", when="@develop")

    depends_on("mpi", when="+mpi")

    with when("+chai"):
      depends_on("chai+mpi", when="+mpi")
      depends_on(f"chai@{chai_version}+raja cxxstd={cxxstd}", when="@develop")
      depends_on("chai@2025.12.0+raja", when="@2025.12.0")
      depends_on("chai@2024.07.0+raja", when="@1.2.7.0:2025.07.0")
      depends_on("fmt@9.1", when=f"^chai@2024.07.0")

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

      depends_on(f"umpire@{umpire_version}", when="@develop")
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

      conflicts("^blt@0.7:", when="^chai@:2024.07.0")

    depends_on("caliper", when="+caliper")
    depends_on("adiak@0.4:", when="+caliper")
    conflicts("^blt@:0.3.6", when="+rocm")

    depends_on("blt@0.6.2:", type="build", when=f"@1.2.7:")

    with when("+cuda~chai"):
        depends_on(f"umpire@{umpire_version}", when="@develop")
        depends_on("umpire+cuda")
        for sm_ in CudaPackage.cuda_arch_values:
            depends_on("umpire cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))

    with when("+rocm~chai"):
        depends_on(f"umpire@{umpire_version}", when="@develop")
        depends_on("umpire+rocm")
        for arch in ROCmPackage.amdgpu_targets:
            depends_on("umpire amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))

    depends_on("raja+openmp", when="+openmp")
    depends_on("raja~openmp", when="~openmp")

    depends_on("raja+cuda", when="+cuda")
    depends_on("raja~cuda", when="~cuda")
    for sm_ in CudaPackage.cuda_arch_values:
        depends_on("raja cuda_arch={0}".format(sm_), when="cuda_arch={0}".format(sm_))

    depends_on("raja+rocm", when="+rocm")
    depends_on("raja~rocm", when="~rocm")
    for arch in ROCmPackage.amdgpu_targets:
        depends_on("raja amdgpu_target={0}".format(arch), when="amdgpu_target={0}".format(arch))

    @property
    def cxx_std(self):
        return self.spec.variants.get("cxxstd").value

    def setup_build_environment(self, env):
        spec = self.spec
        if "+cuda" in spec:
            env.set("CUDAHOSTCXX", self.spec["mpi"].mpicxx)

    def setup_run_environment(self, env):
      super().setup_run_environment(env)

      if self.compiler.extra_rpaths:
        for rpath in self.compiler.extra_rpaths:
          env.prepend_path("LD_LIBRARY_PATH", rpath)

    def cmake_args(self):
        spec = self.spec
        args = []

        args.extend(
            [
                "-Dcamp_DIR=%s" % self.spec["camp"].prefix,
                "-DBLT_SOURCE_DIR=%s" % self.spec["blt"].prefix,
                "-DRAJA_DIR=%s" % self.spec["raja"].prefix,
                "-DBLT_CXX_STD=%s" % f"c++{self.cxx_std}",
                "-DMPI_CXX_LINK_FLAGS='%s'" % self.spec['mpi'].libs.ld_flags,
            ]
        )

        args.append(self.define_from_variant("ENABLE_CHAI", "chai"))
        if "+chai" in spec:
            args.extend(
                [
                    "-Dchai_DIR=%s" % self.spec["chai"].prefix,
                    "-Dumpire_DIR=%s" % self.spec["umpire"].prefix,
                ]
            )

        args.append(self.define_from_variant("ENABLE_GPU_AWARE_MPI", "gpu-aware-mpi"))
        args.append(self.define_from_variant("ENABLE_OPENMP", "openmp"))
        args.append(self.define_from_variant("ENABLE_CALIPER", "caliper"))

        args.append(self.define_from_variant("ENABLE_MPI", "mpi"))
        if "+mpi" in spec:
            args.append(self.define("CMAKE_CXX_COMPILER", self.spec["mpi"].mpicxx))

        args.append(self.define_from_variant("ENABLE_HIP", "rocm"))
        if "+rocm" in spec:
            # Set up the hip macros needed by the build
            args.append("-Dumpire_DIR=%s" % self.spec["umpire"].prefix)
            args.append("-DHIP_ROOT_DIR={0}".format(spec["hip"].prefix))
            rocm_archs = spec.variants["amdgpu_target"].value
            if "none" not in rocm_archs:
                arch_str = ",".join(rocm_archs)
                args.append("-DHIP_HIPCC_FLAGS=--amdgpu-target={0}".format(arch_str))
                args.append("-DCMAKE_HIP_ARCHITECTURES={0}".format(arch_str))

        args.append(self.define_from_variant("ENABLE_CUDA", "cuda"))
        if "+cuda" in spec:
            args.append("-Dumpire_DIR=%s" % self.spec["umpire"].prefix)
            args.append(self.define("CMAKE_CUDA_HOST_COMPILER", self.spec["mpi"].mpicxx))
            if not spec.satisfies("cuda_arch=none"):
                cuda_arch = spec.variants["cuda_arch"].value
                args.append("-DCUDA_ARCH={0}".format(cuda_arch[0]))
                args.append("-DCMAKE_CUDA_ARCHITECTURES={0}".format(cuda_arch[0]))
            args.append(
                "-DCMAKE_CUDA_FLAGS=--extended-lambda -I=%s"
                % (self.spec["mpi"].prefix.include)
            )

        return args

    def install(self, spec, prefix):
        # Kripke does not provide install target, so we have to copy
        # things into place.
        mkdirp(prefix.bin)
        install(join_path(self.build_directory, "kripke.exe"), prefix.bin)
