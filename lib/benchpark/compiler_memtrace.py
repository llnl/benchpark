# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.error import BenchparkError
from benchpark.experiment_helper import ExperimentHelper


class CompilerMemtrace:
    variant(
        "compiler_memtrace",
        default="none",
        values=("none", "baseline", "count", "trace"),
        description="HIP memory tracing (trace runs count and trace builds)",
    )

    class Helper(ExperimentHelper):
        def selected_mode(self):
            mode = self.spec.variants["compiler_memtrace"][0]
            if mode != "none":
                if not self.spec.satisfies("+rocm"):
                    raise BenchparkError("compiler_memtrace requires +rocm")
                if self.spec.variants["package_manager"][0] != "spack":
                    raise BenchparkError(
                        "compiler_memtrace requires package_manager=spack"
                    )
                if not self.spec.satisfies("compiler_attribution=none"):
                    raise BenchparkError(
                        "compiler_memtrace and compiler_attribution require separate experiments"
                    )
            return mode

        def get_helper_name_prefix(self):
            mode = self.selected_mode()
            return f"memtrace_{mode}" if mode != "none" else None

        def compute_modifiers_section(self):
            mode = self.selected_mode()
            return (
                [{"name": "compiler_memtrace", "mode": mode}] if mode != "none" else []
            )

        def compute_package_section(self):
            if self.selected_mode() == "none":
                return {}
            return {
                "packages": {
                    "memtrace_llvm": {
                        "spack_pkg_spec": "memtrace-llvm +runtime +python",
                        "compiler": "default-compiler",
                    }
                }
            }
