# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


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

    depends_on('chai@2024.02', when='@develop')

    depends_on("mpi", when="+mpi")
    depends_on("chai+mpi", when="+mpi")
    depends_on("caliper", when="+caliper")
    depends_on("adiak@0.4:", when="+caliper")
    conflicts("^blt@:0.3.6", when="+rocm")

    aligned_versions = ["2024.02"]
    for v in aligned_versions:
      depends_on(f"raja@{v}~exercises~examples", when=f"^chai@{v}")
      depends_on(f"umpire@{v}~examples", when=f"^chai@{v}")
      depends_on(f"chai@{v}~examples+raja", when=f"^chai@{v}")
      depends_on(f"camp@{v}", when=f"^chai@{v}")

    depends_on("blt@0.6.2:", type="build", when=f"@1.2.7:")

    depends_on("chai+openmp", when="+openmp")
    depends_on("chai~openmp", when="~openmp")
    depends_on("chai+cuda", when="+cuda")
    depends_on("chai~cuda", when="~cuda")

    for arch in ("none", "50", "60", "70", "80"):
        depends_on(f"chai cuda_arch={arch}", when=f"cuda_arch={arch}")

    depends_on("chai+rocm", when="+rocm")
    depends_on("chai~rocm", when="~rocm")
    for target in ("none", "gfx803", "gfx900", "gfx906", "gfx908", "gfx90a", "gfx942"):
        depends_on(f"chai amdgpu_target={target}", when=f"amdgpu_target={target}")

    depends_on("umpire+openmp", when="+openmp")
    depends_on("umpire~openmp", when="~openmp")
    depends_on("umpire+cuda", when="+cuda")
    depends_on("umpire~cuda", when="~cuda")
    depends_on("umpire+rocm", when="+rocm")
    depends_on("umpire~rocm", when="~rocm")

    def setup_build_environment(self, env):
        spec = self.spec
        if "+cuda" in spec:
            env.set("CUDAHOSTCXX", self.spec["mpi"].mpicxx)

    def cmake_args(self):
        spec = self.spec
        args = []

        args.extend(
            [
                "-DCAMP_DIR=%s" % self.spec["camp"].prefix,
                "-DBLT_SOURCE_DIR=%s" % self.spec["blt"].prefix,
                "-Dumpire_DIR=%s" % self.spec["umpire"].prefix,
                "-DRAJA_DIR=%s" % self.spec["raja"].prefix,
                "-Dchai_DIR=%s" % self.spec["chai"].prefix,
                "-DENABLE_CHAI=ON",
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
                args.append("-DHIP_HIPCC_FLAGS=--amdgpu-target={0}".format(",".join(rocm_archs)))
                args.append("-DCMAKE_HIP_ARCHITECTURES={0}".format(rocm_archs))
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
                "-DCMAKE_CUDA_FLAGS=--extended-lambda -I%s -I=%s"
                % (self.spec["cub"].prefix.include, self.spec["mpi"].prefix.include)
            )
        else:
            args.append("-DENABLE_CUDA=OFF")

        return args

    def install(self, spec, prefix):
        # Kripke does not provide install target, so we have to copy
        # things into place.
        mkdirp(prefix.bin)
        install(join_path(self.build_directory, "kripke.exe"), prefix.bin)
