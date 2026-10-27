# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shlex

from spack.package import *
from spack_repo.builtin.build_systems.cmake import CMakePackage


class MemtraceLlvm(CMakePackage):
    """LLVM memory-operation catalog, HIP count/trace runtime, and Python reader."""

    homepage = "https://github.com/llnl/benchpark-llvm"
    git = "git@github.com:llnl/benchpark-llvm.git"

    maintainers("yejashi")

    license("Apache-2.0 WITH LLVM-exception")

    # PR #8, memtrace-llvm-impl. develop does not yet contain this source tree.
    version("0.1.0", commit="e229827a58479ba87a1efd0b1255a8ad6eb911d5")

    root_cmakelists_dir = "memtrace-llvm/plugin"
    variant("runtime", default=True, description="Build the HIP interposition runtime")
    variant(
        "python", default=True, description="Install the Python reader and memtrace CLI"
    )

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("cmake@3.16:", type="build")
    depends_on("nlohmann-json@3.11.3:")
    depends_on("hip@6.4:", when="+runtime", type=("build", "link", "run"))
    depends_on("python@3.8:", when="+python", type=("build", "run"))
    depends_on("py-numpy@1.24:", when="+python", type="run")

    requires(
        "%llvm",
        "%llvm-amdgpu",
        "%rocmcc",
        "%cce",
        policy="any_of",
        msg="memtrace-llvm needs a Clang compiler with LLVM >=19 development files",
    )

    @property
    def llvm_dir(self):
        # A separately concretized llvm dependency can have an incompatible ABI.
        # Use the LLVM shipped with the compiler that will load the pass.
        prefix = self.spec["cxx"].prefix
        for suffix in (
            "lib/cmake/llvm",
            "lib64/cmake/llvm",
            "llvm/lib/cmake/llvm",
            "cce-clang/x86_64/lib/cmake/llvm",
        ):
            path = join_path(prefix, suffix)
            if os.path.isfile(join_path(path, "LLVMConfig.cmake")):
                return path
        raise InstallError(
            f"No LLVM CMake configuration under compiler prefix {prefix}"
        )

    def cmake_args(self):
        # Upstream CMake enforces LLVM >=19, including for versioned ROCm compilers.
        return [
            self.define("LLVM_DIR", self.llvm_dir),
            self.define("CMAKE_INSTALL_LIBDIR", "lib"),
            self.define_from_variant("MEMTRACE_BUILD_RUNTIME", "runtime"),
        ]

    @property
    def sanity_check_is_file(self):
        files = [
            "lib/MemTracePlugin.so",
            "lib/cmake/MemTracePlugin/MemTracePluginConfig.cmake",
            "include/memtrace_device.h",
            "include/memtrace_host.h",
            "include/memtrace_abi.h",
        ]
        if self.spec.satisfies("+runtime"):
            files.append("lib/libmemtrace_runtime.so")
        if self.spec.satisfies("+python"):
            files.extend(
                [
                    "bin/memtrace",
                    "share/memtrace/python/memtrace/__init__.py",
                    "share/memtrace/reader_cli.py",
                    "share/memtrace/reader.json",
                ]
            )
        return files

    def reader_paths(self):
        python = self.spec["python"].package
        return [join_path(self.prefix.share, "memtrace", "python")] + [
            join_path(self.spec["py-numpy"].prefix, path)
            for path in dict.fromkeys((python.purelib, python.platlib))
        ]

    def reader_preload(self):
        """Load all MKL DSOs before NumPy built with Meson and lld is imported."""
        numpy = self.spec["py-numpy"]
        if "blas" not in numpy or numpy["blas"].name not in (
            "intel-oneapi-mkl",
            "intel-mkl",
            "intel-parallel-studio",
        ):
            return []
        return [
            str(path)
            for path in numpy["blas"].libs.files
            if os.path.basename(str(path)).startswith("libmkl_")
        ]

    @run_after("install")
    def install_reader(self):
        if not self.spec.satisfies("+python"):
            return
        destination = join_path(self.prefix.share, "memtrace", "python", "memtrace")
        install_tree(
            join_path(self.stage.source_path, "memtrace-llvm", "python", "memtrace"),
            destination,
        )
        reader_root = join_path(self.prefix.share, "memtrace")
        install(
            join_path(os.path.dirname(__file__), "reader_cli.py"),
            join_path(reader_root, "reader_cli.py"),
        )
        with open(join_path(reader_root, "reader.json"), "w") as stream:
            json.dump(
                {"paths": self.reader_paths(), "preload": self.reader_preload()},
                stream,
            )
        mkdirp(self.prefix.bin)
        cli = join_path(self.prefix.bin, "memtrace")
        with open(cli, "w") as stream:
            stream.write(
                "#!/bin/sh\nexec "
                + shlex.quote(self.spec["python"].command.path)
                + " "
                + shlex.quote(join_path(reader_root, "reader_cli.py"))
                + ' "$@"\n'
            )
        set_executable(cli)

    def setup_run_environment(self, env):
        env.prepend_path("CMAKE_PREFIX_PATH", self.prefix)
        env.set(
            "MEMORY_TRACE_PLUGIN_DIR",
            join_path(self.prefix.lib, "cmake", "MemTracePlugin"),
        )
        env.set(
            "MEMORY_TRACE_PLUGIN_PATH", join_path(self.prefix.lib, "MemTracePlugin.so")
        )
        env.set(
            "MEMORY_TRACE_DEVICE_HEADER",
            join_path(self.prefix.include, "memtrace_device.h"),
        )
        if self.spec.satisfies("+runtime"):
            env.set(
                "MEMORY_TRACE_RUNTIME_PATH",
                join_path(self.prefix.lib, "libmemtrace_runtime.so"),
            )
        if self.spec.satisfies("+python"):
            env.prepend_path("PATH", self.prefix.bin)
            for path in reversed(self.reader_paths()):
                env.prepend_path("PYTHONPATH", path)
            for path in reversed(self.reader_preload()):
                env.prepend_path("LD_PRELOAD", path, separator=" ")
