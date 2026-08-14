# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import re

from spack.package import *
from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage


class Hecbench(CMakePackage, CudaPackage, ROCmPackage):
    """HeCBench heterogeneous computing benchmark suite."""

    homepage = "https://github.com/ORNL/HeCBench"
    git = "https://github.com/ORNL/HeCBench.git"
    tags = ["benchmark"]

    license("BSD-3-Clause")

    version("2026-08-13", commit="f9540404573a2be7ad1d1ee4b3106fd064825fa8")
    patch("select-benchmark.patch")
    patch("find-hipcc.patch")

    variant(
        "benchmark",
        default="babelstream",
        values=("babelstream",),
        multi=False,
        description="HeCBench benchmark to build",
    )
    variant(
        "cuda_arch",
        default="none",
        values=("none",) + CudaPackage.cuda_arch_values,
        multi=False,
        sticky=True,
        when="+cuda",
        description="CUDA architecture",
    )
    variant(
        "amdgpu_target",
        default="none",
        values=("none",) + ROCmPackage.amdgpu_targets,
        multi=False,
        sticky=True,
        when="+rocm",
        description="AMD GPU architecture",
    )

    requires(
        "+cuda",
        "+rocm",
        policy="one_of",
        msg="Select exactly one programming model: +cuda or +rocm",
    )
    conflicts(
        "cuda_arch=none",
        when="+cuda",
        msg="CUDA builds require exactly one cuda_arch, e.g. cuda_arch=80",
    )

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("cmake@3.21:", type="build")

    # Minimum toolkit versions documented for the pinned HeCBench revision.
    depends_on("hip@7.0:+rocm", when="+rocm")
    depends_on("cuda@12.2:", when="+cuda")

    def selected_benchmark(self):
        return self.spec.variants["benchmark"].value

    def selected_model(self):
        if "+rocm" in self.spec:
            return "hip"
        if "+cuda" in self.spec:
            return "cuda"
        raise InstallError("No HeCBench programming model selected")

    def selected_target(self):
        return "{0}-{1}".format(self.selected_benchmark(), self.selected_model())

    def cmake_args(self):
        spec = self.spec
        args = [
            self.define("HECBENCH_ENABLE_CUDA", "+cuda" in spec),
            self.define("HECBENCH_ENABLE_HIP", "+rocm" in spec),
            self.define("HECBENCH_ENABLE_OPENMP", False),
            self.define("HECBENCH_ENABLE_SYCL", False),
            self.define("HECBENCH_ENABLE_TESTING", False),
            self.define("HECBENCH_BUILD_ALL_BENCHMARKS", False),
            self.define("HECBENCH_BENCHMARK", self.selected_benchmark()),
        ]

        if "+rocm" in spec:
            amdgpu_target = spec.variants["amdgpu_target"].value
            args.extend(
                [
                    self.define("HECBENCH_HIP_ARCH", amdgpu_target),
                    self.define("CMAKE_HIP_ARCHITECTURES", amdgpu_target),
                    self.define(
                        "CMAKE_HIP_COMPILER",
                        join_path(spec["llvm-amdgpu"].prefix.bin, "amdclang++"),
                    ),
                    self.define("HIP_COMPILER", join_path(spec["hip"].prefix.bin, "hipcc")),
                ]
            )

        if "+cuda" in spec:
            cuda_arch = spec.variants["cuda_arch"].value
            args.extend(
                [
                    self.define("HECBENCH_CUDA_ARCH", cuda_arch),
                    self.define("CMAKE_CUDA_ARCHITECTURES", cuda_arch),
                    self.define("CMAKE_CUDA_COMPILER", join_path(spec["cuda"].prefix.bin, "nvcc")),
                    self.define("CUDAToolkit_ROOT", spec["cuda"].prefix),
                ]
            )

        return args

    @property
    def build_targets(self):
        return [self.selected_target()]

    def install(self, spec, prefix):
        model = self.selected_model()
        benchmark = self.selected_benchmark()
        built_binary = join_path(self.build_directory, "bin", model, benchmark)
        if not os.path.isfile(built_binary):
            raise InstallError("Expected HeCBench binary was not found: {0}".format(built_binary))

        mkdirp(prefix.bin)
        install(built_binary, join_path(prefix.bin, self.selected_target()))

    def test_babelstream(self):
        """Run BabelStream and verify its float and double results."""
        executable = Executable(join_path(self.prefix.bin, self.selected_target()))
        output = executable("--arraysize", "1048576", "--numtimes", "2", output=str, error=str)
        results = re.findall(r"^(PASS|FAIL)$", output, re.MULTILINE)
        if results != ["PASS", "PASS"]:
            raise RuntimeError(
                "Expected BabelStream validation results ['PASS', 'PASS'], got {0}".format(results)
            )
