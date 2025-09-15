# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
from spack_repo.builtin.packages.boost.package import Boost

import os


class Branson(CMakePackage, CudaPackage, ROCmPackage):
    """Branson's purpose is to study different algorithms for parallel Monte
    Carlo transport. Currently it contains particle passing and mesh passing
    methods for domain decomposition."""

    homepage = "https://github.com/lanl/branson"
    url = "https://github.com/lanl/branson/archive/0.82.tar.gz"
    git = "https://github.com/lanl/branson.git"

    tags = ["proxy-app"]

    license("MIT")

    version("develop", branch="develop")

    version("1.01", sha256="90208eaec4f6d64a4fd81cd838e30b5e7207246cb7f407e482965f23bbcee848")
    version(
        "0.82",
        sha256="7d83d41d0c7ab9c1c906a902165af31182da4604dd0b69aec28d709fe4d7a6ec",
        preferred=True,
    )
    version("0.81", sha256="493f720904791f06b49ff48c17a681532c6a4d9fa59636522cf3f9700e77efe4")
    version("0.8", sha256="85ffee110f89be00c37798700508b66b0d15de1d98c54328b6d02a9eb2cf1cb8")

    variant("openmp", default=False, description="Enable OpenMP support")
    variant("caliper", default=False, description="Enable Caliper monitoring")
    variant("metis", default=False, description="Enable METIS")
    variant("viz", default=False, description="Enable VIZ")
    variant("n_groups", default=30, values=int, description="Number of groups")

    depends_on("c", type="build")
    depends_on("cxx", type="build")

    #depends_on("mpi")
    depends_on("mpi@2:")

    # TODO: replace this with an explicit list of components of Boost,
    # for instance depends_on('boost +filesystem')
    # See https://github.com/spack/spack/pull/22303 for reference
    depends_on(Boost.with_default_variants, when="@:0.81")
    depends_on("metis")
    depends_on("parmetis", when="@:0.81")
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")

    root_cmakelists_dir = "src"

    flag_handler = build_system_flags

    patch("branson_cmake.patch")
    patch("branson_power9.patch")

    def setup_build_environment(self, env):
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def patch(self):
        ppu_intrinsics_file = os.path.join(self.stage.source_path, "src", "random123", "features", "ppu_intrinsics.h")
        with open(ppu_intrinsics_file , "w") as f:
            pass

    def cmake_args(self):
        spec = self.spec
        args = []

        args.append(f"-DMPI_C_COMPILER={spec['mpi'].mpicc}")
        args.append(f"-DMPI_CXX_COMPILER={spec['mpi'].mpicxx}")
        args.append(f"-DCMAKE_Fortran_COMPILER={spec['mpi'].mpifc}")

        args.append(self.define_from_variant("ENABLE_METIS", "metis"))
        args.append(f"-DMETIS_ROOT_DIR={spec['metis'].prefix}")

        args.append(self.define_from_variant("ENABLE_VIZ", "viz"))

        if '+cuda' in spec:
            args.append("-DENABLE_CUDA=ON")
            args.append(f"-DCMAKE_CUDA_COMPILER={spec['cuda'].prefix}/bin/nvcc")
            cuda_arch_vals = spec.variants["cuda_arch"].value
            if cuda_arch_vals:
              cuda_arch_sorted = list(sorted(cuda_arch_vals, reverse=True))
              cuda_arch = cuda_arch_sorted[0]
              args.append(f"-DCUDA_ARCH={cuda_arch}")
        else:
            args.append("-DENABLE_CUDA=OFF")

        if '+rocm' in spec:
            args.append("-DENABLE_HIP=ON")
            rocm_arch_vals = spec.variants["amdgpu_target"].value
            args.append(f"-DROCM_PATH={spec['hip'].prefix}")
            args.append(f"-DHIP_PATH={spec['hip'].prefix}/hip")
            if rocm_arch_vals:
              rocm_arch_sorted = list(sorted(rocm_arch_vals, reverse=True))
              rocm_arch = rocm_arch_sorted[0]
              args.append(f"-DROCM_ARCH={rocm_arch}")
              args.append(f"-DHIP_ARCH={rocm_arch}")
        else:
            args.append("-DENABLE_HIP=OFF")

        args.append(self.define_from_variant("ENABLE_OPENMP", "openmp"))

        if '+caliper' in spec:
            args.append(self.define_from_variant("ENABLE_CALIPER", "caliper"))
            args.append(f"-Dcaliper_DIR={spec['caliper'].prefix}")

        args.append("-DBUILD_TESTING=OFF")
        args.append(f"-DN_GROUPS={self.spec.variants['n_groups'].value}")

        args.append(f"-DMPI_CXX_LINK_FLAGS={spec['mpi'].libs.ld_flags}")

        return args

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        mkdir(prefix.doc)
        install(join_path(self.build_directory, "BRANSON"), prefix.bin)
        install("LICENSE.md", prefix.doc)
        install("README.md", prefix.doc)
        install_tree("inputs", prefix.inputs)
