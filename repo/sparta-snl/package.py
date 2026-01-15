# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from spack.package import *


class SpartaSnl(CMakePackage, CudaPackage, ROCmPackage):

    homepage = "https://sparta.github.io/"
    git = "https://github.com/sparta/sparta.git"

    version("master", branch="master")
    version("20Jan2025", tag="20Jan2025")

    variant("mpi", default=True, description="Build with mpi")
    variant("openmp", default=False, description="Enable OpenMP support")
    variant("jpeg", default=False, description="Build with jpeg support")
    variant("png", default=False, description="Build with png support")

    variant(
        "kokkos",
        default=True,
        description="Build with KOKKOS"
    )

    variant(
        "fft",
        default="fftw3",
        description="Which FFT library to use",
        values=("fftw3", "mkl", "kiss"),
        multi=False,
    )

    variant(
        "fft_kokkos",
        default="fftw3",
        when="+kokkos",
        description="FFT library for Kokkos package",
        values=("kiss", "fftw3", "mkl", "hipfft", "cufft"),
        multi=False,
    )

    depends_on("c", type="build")
    depends_on("cxx", type="build")

    depends_on("mpi", when="+mpi")

    depends_on("kokkos", when="+kokkos")
    depends_on("kokkos+openmp cxxstd=17", when="+openmp")
    depends_on("kokkos+rocm", when="+rocm")
    depends_on("kokkos+wrapper+cuda cxxstd=17", when="+cuda")
    # Kokkos 5 not building
    depends_on("kokkos@:4", when="+kokkos")

    depends_on("jpeg", when="+jpeg")
    depends_on("libpng", when="+png")

    depends_on("fftw-api@3", when="fft=fftw3")
    depends_on("mkl", when="fft=mkl")

    depends_on("hipfft", when="+kokkos+rocm fft_kokkos=hipfft")
    depends_on("fftw-api@3", when="+kokkos fft_kokkos=fftw3")
    depends_on("mkl", when="+kokkos fft_kokkos=mkl")
    depends_on("kokkos+shared@3.1:", when="+kokkos")

    for arch in CudaPackage.cuda_arch_values:
        depends_on("kokkos+cuda cuda_arch=%s" % arch, when="+kokkos+cuda cuda_arch=%s" % arch)

    for arch in ROCmPackage.amdgpu_targets:
        depends_on(
            "kokkos+rocm amdgpu_target=%s" % arch, when="+kokkos+rocm amdgpu_target=%s" % arch
        )

    conflicts("+rocm", when="+cuda")
    conflicts("+cuda", when="+rocm")

    def setup_run_environment(self, env):
        if self.spec.satisfies("+kokkos+rocm fft_kokkos=hipfft"):
            env.prepend_path("LD_LIBRARY_PATH", self.spec["hipfft"].prefix.lib)

    def setup_build_environment(self, env):
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")
        if self.spec.satisfies("+kokkos+rocm fft_kokkos=hipfft"):
            env.prepend_path("LD_LIBRARY_PATH", self.spec["hipfft"].prefix.lib)
        if "+mpi" in self.spec:
            if self.spec["mpi"].extra_attributes and "ldflags" in self.spec["mpi"].extra_attributes:
                env.append_flags("LDFLAGS", self.spec["mpi"].extra_attributes["ldflags"])

    root_cmakelists_dir = "cmake"

    def flag_handler(self, name, flags):
        wrapper_flags = []
        build_system_flags = []

        if self.spec.satisfies("+mpi+cuda") or self.spec.satisfies("+mpi+rocm"):
            if self.spec.satisfies("^[virtuals=mpi] cray-mpich"):
                gtl_lib = self.spec["cray-mpich"].package.gtl_lib
                build_system_flags.extend(gtl_lib.get(name) or [])
            # hipcc is not wrapped, we need to pass the flags via the build
            # system.
            build_system_flags.extend(flags)
        else:
            wrapper_flags.extend(flags)

        return (wrapper_flags, [], build_system_flags)

    def cmake_args(self):
        spec = self.spec
    
        args = [
            self.define("SPARTA_LIST_PKGS", False),
            self.define("SPARTA_LIST_TPLS", False),
            self.define("SPARTA_ENABLE_TESTING", False),
            self.define("SPARTA_ENABLE_PARAVIEW_TESTING", False),
            self.define("CMAKE_CXX_STANDARD", 17),
        ]

        if spec.satisfies("+mpi"):
            args.append(self.define_from_variant("BUILD_MPI", "mpi"))
            args.append(self.define("PKG_MPI_STUBS", False))
            args.append(f"-DMPI_ROOT={spec['mpi'].prefix}")
            args.append(f"-DMPI_CXX_LINK_FLAGS='{spec['mpi'].libs.ld_flags}'")
            args.append(f"-DMPI_C_COMPILER={spec['mpi'].mpicc}")
            args.append(f"-DMPI_CXX_COMPILER={spec['mpi'].mpicxx}")

        if spec.satisfies("+jpeg"):
            args.append(self.define_from_variant("BUILD_JPEG", "jpeg"))
            args.append(f"-DJPEG_ROOT='{spec['jpeg'].prefix}'")
        if spec.satisfies("+png"):
            args.append(self.define_from_variant("BUILD_PNG", "png"))
            args.append(f"-DPNG_ROOT='{spec['libpng'].prefix}'")

        args.append(self.define("PKG_FFT", True))
        args.append(f"-DFFT={spec.variants['fft'].value.upper()}")

        if spec.satisfies("+kokkos"):
            args.append(self.define("PKG_KOKKOS", True))
            args.append(self.define("USE_EXTERNAL_KOKKOS", True))
            args.append(f"-DFFT_KOKKOS={spec.variants['fft_kokkos'].value.upper()}")
        else:
            args.append(self.define("PKG_KOKKOS", False))

        return args

    def install(self, spec, prefix):
        super().install(spec, prefix)
        install_tree("examples", prefix.examples)
