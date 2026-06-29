# Copyright Spack Project Developers.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
from spack.package import *

from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.build_systems.cuda import CudaPackage


class Hecbench(CMakePackage, CudaPackage):
    """HeCBench heterogeneous computing benchmark suite.

    This preliminary package builds exactly one HeCBench benchmark for exactly
    one programming model at a time.

    Example:
        hecbench +cuda benchmark=babelstream cuda_arch=90

    This maps to the CMake build target:
        babelstream-cuda
    """

    homepage = "https://github.com/zjin-lcf/HeCBench"
    git = "https://github.com/zjin-lcf/HeCBench.git"

    license("BSD-3-Clause")

    # Development-oriented version for the preliminary package.
    # We can replace this later with a fixed tag/tarball or pinned commit.
    version("master", branch="master")

    variant(
        "benchmark",
        values=str,
        default="none",
        multi=False,
        description="HeCBench benchmark to build",
    )

    # -------------------------------------------------------------------------
    # Programming model selection
    #
    # +cuda and cuda_arch are inherited from CudaPackage.
    # The other HeCBench programming models are represented explicitly here.
    # We will validate CUDA first, then refine HIP/OpenMP/SYCL behavior.
    # -------------------------------------------------------------------------

    variant("hip", default=False, description="Build the HIP benchmark variant")
    variant("openmp", default=False, description="Build the OpenMP benchmark variant")
    variant("sycl", default=False, description="Build the SYCL benchmark variant")

    variant(
        "hip_arch",
        values=str,
        default="none",
        multi=False,
        description="HIP target architecture, e.g. gfx90a or gfx942",
    )

    # A benchmark name must be provided
    conflicts(
        "benchmark=none",
        msg="Select a HeCBench benchmark with benchmark=<name>",
    )

    conflicts(
        "cuda_arch=none",
        when="+cuda",
        msg="CUDA builds require cuda_arch=<arch>, e.g. cuda_arch=90",
    )

    # Exactly one programming model should be selected
    requires(
        "+cuda",
        "+hip",
        "+openmp",
        "+sycl",
        policy="one_of",
        msg="Select exactly one programming model: +cuda, +hip, +openmp, or +sycl",
    )

    # HIP requires a target architecture.
    conflicts(
        "hip_arch=none",
        when="+hip",
        msg="HIP builds require hip_arch=<gfx target>, e.g. hip_arch=gfx90a",
    )

    # -------------------------------------------------------------------------
    # Dependencies
    # -------------------------------------------------------------------------

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    # HeCBench's top-level CMakeLists requires CMake 3.21+.
    depends_on("cmake@3.21:", type="build")

    # CudaPackage provides +cuda, cuda_arch, and CUDA dependency

    def selected_benchmark(self):
        return self.spec.variants["benchmark"].value

    def selected_model(self):
        if "+cuda" in self.spec:
            return "cuda"
        if "+hip" in self.spec:
            return "hip"
        if "+openmp" in self.spec:
            return "omp"
        if "+sycl" in self.spec:
            return "sycl"

        # This should be unreachable because of the requires(... one_of ...) above.
        raise InstallError(
            "No HeCBench programming model selected. "
            "Use one of +cuda, +hip, +openmp, or +sycl."
        )

    def selected_target(self):
        return "{0}-{1}".format(
            self.selected_benchmark(),
            self.selected_model(),
        )

    def selected_source_dir(self):
        return join_path(
            self.stage.source_path,
            "src",
            "{0}-{1}".format(
                self.selected_benchmark(),
                self.selected_model(),
            ),
        )

    # -------------------------------------------------------------------------
    # CMake configuration
    # -------------------------------------------------------------------------

    # def cmake_args(self):
    #     spec = self.spec

    #     source_dir = self.selected_source_dir()
    #     if not isdir(source_dir):
    #         raise InstallError(
    #             "HeCBench benchmark/model source directory does not exist: {0}".format(
    #                 source_dir
    #             )
    #         )

    #     args = [
    #         self.define("HECBENCH_ENABLE_CUDA", "+cuda" in spec),
    #         self.define("HECBENCH_ENABLE_HIP", "+hip" in spec),
    #         self.define("HECBENCH_ENABLE_SYCL", "+sycl" in spec),
    #         self.define("HECBENCH_ENABLE_OPENMP", "+openmp" in spec),
    #         self.define("HECBENCH_ENABLE_TESTING", False),
    #         self.define("HECBENCH_BUILD_ALL_BENCHMARKS", False),
    #     ]

    #     # CUDA configuration
    #     if "+cuda" in spec:
    #         cuda_arch = spec.variants["cuda_arch"].value

    #         if not cuda_arch:
    #             raise InstallError(
    #                 "CUDA builds require cuda_arch=<arch>, e.g. cuda_arch=90"
    #             )

    #         # HeCBench's CMake expects numeric architecture values such as "90".
    #         args.append(self.define("HECBENCH_CUDA_ARCH", cuda_arch[0]))

    #         # Force CMake to use the CUDA toolkit chosen by Spack.
    #         args.append(
    #             self.define(
    #                 "CUDAToolkit_ROOT",
    #                 spec["cuda"].prefix,
    #             )
    #         )
    #         args.append(
    #             self.define(
    #                 "CMAKE_CUDA_COMPILER",
    #                 join_path(spec["cuda"].prefix.bin, "nvcc"),
    #             )
    #         )

    #     # HIP configuration: structurally wired, not yet validated.
    #     if "+hip" in spec:
    #         args.append(
    #             self.define(
    #                 "HECBENCH_HIP_ARCH",
    #                 spec.variants["hip_arch"].value,
    #             )
    #         )

    #     # OpenMP and SYCL will need toolchain-specific refinement later,
    #     # but the package-level programming model interface is established here.

    #     return args
    def cmake_args(self):
        spec = self.spec

        source_dir = self.selected_source_dir()
        if not os.path.isdir(source_dir):
            raise InstallError(
                "HeCBench benchmark/model source directory does not exist: {0}".format(
                    source_dir
                )
            )

        args = [
            self.define("HECBENCH_ENABLE_CUDA", "+cuda" in spec),
            self.define("HECBENCH_ENABLE_HIP", "+hip" in spec),
            self.define("HECBENCH_ENABLE_SYCL", "+sycl" in spec),
            self.define("HECBENCH_ENABLE_OPENMP", "+openmp" in spec),
            self.define("HECBENCH_ENABLE_TESTING", False),
        ]

        if "+cuda" in spec:
            cuda_arch = spec.variants["cuda_arch"].value

            if not cuda_arch:
                raise InstallError(
                    "CUDA builds require cuda_arch=<arch>, e.g. cuda_arch=90"
                )

            args.append(self.define("HECBENCH_CUDA_ARCH", cuda_arch[0]))

            args.append(
                self.define(
                    "CUDAToolkit_ROOT",
                    spec["cuda"].prefix,
                )
            )

            args.append(
                self.define(
                    "CMAKE_CUDA_COMPILER",
                    join_path(spec["cuda"].prefix.bin, "nvcc"),
                )
            )

        if "+hip" in spec:
            args.append(
                self.define(
                    "HECBENCH_HIP_ARCH",
                    spec.variants["hip_arch"].value,
                )
            )

        return args

    # -------------------------------------------------------------------------
    # Build exactly one HeCBench CMake target
    # -------------------------------------------------------------------------

    @property
    def build_targets(self):
        return [self.selected_target()]

    # -------------------------------------------------------------------------
    # Manual installation
    #
    # The HeCBench CMake macro writes binaries to:
    #   <build_dir>/bin/<model>/<benchmark>
    #
    # The CMake files inspected so far do not define install() rules for these
    # binaries, so copy the selected executable into prefix.bin manually.
    # -------------------------------------------------------------------------

    def install(self, spec, prefix):
        benchmark = self.selected_benchmark()
        model = self.selected_model()

        built_binary = join_path(
            self.build_directory,
            "bin",
            model,
            benchmark,
        )

        if not os.path.isfile(built_binary):
            raise InstallError(
                "Expected HeCBench binary was not found: {0}".format(built_binary)
            )

        mkdirp(prefix.bin)

        install(
            built_binary,
            join_path(prefix.bin, "{0}-{1}".format(benchmark, model)),
        )