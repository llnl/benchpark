# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from spack.package import *
from spack_repo.builtin.build_systems.cmake import CMakePackage

CLANG_LIKE_COMPILERS = ("llvm", "llvm-amdgpu", "rocmcc", "cce")


class CompilerAttributionPlugin(CMakePackage):
    """LLVM pass plugin that attributes static compiler evidence to Caliper regions."""

    homepage = "https://github.com/TauferLab/Src_LLNL_Perf_Analysis_with_Compiler_Remarks"
    git = "git@github.com:TauferLab/Src_LLNL_Perf_Analysis_with_Compiler_Remarks.git"

    maintainers("yejashi")

    license("UNKNOWN")

    version("0.1.0", commit="c6e518672d5f2a3aa6f51dcfe191af83dc5affee")

    root_cmakelists_dir = "compiler_attribution_plugin"

    variant(
        "association",
        default=False,
        description="Build association instrumentation and runtime",
    )

    variant(
        "remark_counts",
        default=False,
        description="Collect per-pass optimization remark statistics",
    )
    variant(
        "remark_details",
        default=False,
        description="Collect the full per-remark detail list",
    )
    variant(
        "kru",
        default=False,
        description="Collect HIP backend kernel resource usage metrics",
    )
    variant(
        "ir_metrics",
        default=False,
        description="Collect per-function IR metrics at pipeline phases",
    )
    variant(
        "per_pass_ir_metrics",
        default=False,
        description="Collect IR metric snapshots around each optimization pass",
    )
    variant(
        "ir_phases",
        default="all",
        values=(
            "all",
            "pipeline-start",
            "early-simplification",
            "optimizer-early",
            "optimizer-last",
        ),
        multi=True,
        description="Pipeline phases to capture IR metrics at",
    )

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("cmake@3.16:", type="build")
    depends_on("nlohmann-json@3.11.3:")
    depends_on("caliper@2.12.1:", when="+association")

    requires(
        *(f"%{compiler}" for compiler in CLANG_LIKE_COMPILERS),
        policy="any_of",
        msg="CompilerAttributionPlugin must be built with a Clang-compatible compiler",
    )

    @property
    def sanity_check_is_file(self):
        files = [
            "lib/CompilerAttributionPlugin.so",
            "lib/cmake/CompilerAttributionPlugin/CompilerAttributionPluginConfig.cmake",
        ]
        if self.spec.satisfies("+association"):
            files.append("lib/CaliperAssociationLib.so")
        return files

    @property
    def llvm_dir(self):
        compiler_prefix = self.spec["cxx"].prefix
        candidates = [
            join_path(compiler_prefix, "lib", "cmake", "llvm"),
            join_path(compiler_prefix, "lib64", "cmake", "llvm"),
            join_path(compiler_prefix, "llvm", "lib", "cmake", "llvm"),
            join_path(compiler_prefix, "cce-clang", "x86_64", "lib", "cmake", "llvm"),
        ]
        for candidate in candidates:
            if os.path.isdir(candidate):
                return candidate

        raise InstallError(
            f"Could not find an LLVM CMake package under {compiler_prefix}. "
            "CompilerAttributionPlugin must be built against the LLVM belonging "
            f"to the clang that loads it ({self.spec['cxx'].name})."
        )

    @property
    def plugin_path(self):
        return join_path(self.prefix.lib, "CompilerAttributionPlugin.so")

    @property
    def runtime_path(self):
        return join_path(self.prefix.lib, "CaliperAssociationLib.so")

    @property
    def compile_flags(self):
        flags = f"-fpass-plugin={self.plugin_path} -mllvm -pass-remarks=.*"
        if self.spec.satisfies("+kru"):
            flags += " -mllvm -pass-remarks-analysis=kernel-resource-usage"
        return flags

    @property
    def link_flags(self):
        if not self.spec.satisfies("+association"):
            return ""
        return (
            f"{self.runtime_path} -Wl,-rpath,{self.prefix.lib} "
            "-Wl,--export-dynamic"
        )

    def cmake_args(self):
        return [
            self.define("LLVM_DIR", self.llvm_dir),
            self.define("CMAKE_INSTALL_LIBDIR", "lib"),
            self.define_from_variant(
                "COMPILER_ATTRIBUTION_ENABLE_ASSOCIATION", "association"
            ),
        ]

    def extraction_dir(self, dependent_spec):
        return join_path(dependent_spec.prefix, "share", "compiler-attribution")

    def setup_run_environment(self, env):
        env.prepend_path("CMAKE_PREFIX_PATH", self.prefix)
        env.set(
            "COMPILER_ATTRIBUTION_PLUGIN_DIR",
            join_path(self.prefix.lib, "cmake", "CompilerAttributionPlugin"),
        )
        env.set("COMPILER_ATTRIBUTION_PLUGIN_PATH", self.plugin_path)
        env.set("COMPILER_ATTRIBUTION_CXXFLAGS", self.compile_flags)
        env.set("COMPILER_ATTRIBUTION_LDFLAGS", self.link_flags)
        env.set(
            "COMPILER_ATTRIBUTION_EXTRACTION_DIR",
            join_path(
                self.prefix, "share", "compiler-attribution", "extraction_plugin_output"
            ),
        )
        if self.spec.satisfies("+association"):
            env.set("COMPILER_ATTRIBUTION_RUNTIME_PATH", self.runtime_path)

    def setup_dependent_build_environment(self, env, dependent_spec):
        if not any(
            dependent_spec.satisfies(f"%{compiler}")
            for compiler in CLANG_LIKE_COMPILERS
        ):
            raise InstallError(
                f"{dependent_spec.name} must be built with a Clang-compatible "
                f"compiler ({', '.join(CLANG_LIKE_COMPILERS)}) to load "
                "CompilerAttributionPlugin"
            )

        env.append_flags("SPACK_CXXFLAGS", self.compile_flags)
        env.append_flags("CXXFLAGS", self.compile_flags)
        env.append_flags("HIPFLAGS", self.compile_flags)
        env.prepend_path("CMAKE_PREFIX_PATH", self.prefix)

        source_path = dependent_spec.package.stage.source_path
        env.set("EXTRACTION_SRC_PATH", source_path)

        out_path = self.extraction_dir(dependent_spec)
        mkdirp(out_path)
        env.set("EXTRACTION_OUT_PATH", out_path)

        toggles = {
            "EXTRACTION_REMARK_COUNTS": "+remark_counts",
            "EXTRACTION_REMARK_DETAILS": "+remark_details",
            "EXTRACTION_KRU": "+kru",
            "EXTRACTION_IR_METRICS": "+ir_metrics",
            "EXTRACTION_PER_PASS_IR_METRICS": "+per_pass_ir_metrics",
        }
        for name, variant_spec in toggles.items():
            env.set(name, "ON" if self.spec.satisfies(variant_spec) else "OFF")

        phases = self.spec.variants["ir_phases"].value
        if "all" not in phases:
            env.set("EXTRACTION_IR_PHASES", ":".join(phases))

        if self.spec.satisfies("+association"):
            env.set("ASSOCIATION_SRC_PATH", source_path)
            env.append_flags("SPACK_LDFLAGS", self.link_flags)
            env.append_flags("LDFLAGS", self.link_flags)

    def setup_dependent_run_environment(self, env, dependent_spec):
        env.set(
            "COMPILER_ATTRIBUTION_EXTRACTION_DIR",
            join_path(self.extraction_dir(dependent_spec), "extraction_plugin_output"),
        )
