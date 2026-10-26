# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack_repo.builtin.packages.py_numpy.package import PyNumpy as BuiltinPyNumpy


class PyNumpy(BuiltinPyNumpy):
    """NumPy with complete MKL linkage when built using Meson and lld."""

    def config_settings(self, spec, prefix):
        settings = super().config_settings(spec, prefix)
        if spec.satisfies("@1.26:") and spec["blas"].name in (
            "intel-oneapi-mkl",
            "intel-mkl",
            "intel-parallel-studio",
        ):
            # lld otherwise drops MKL's threading/core DSOs, whose symbols are
            # referenced by the interface DSO. Spack appends spec ldflags after
            # the library arguments, too late for --no-as-needed to retain them.
            settings["setup-args"]["-Db_asneeded"] = False
        return settings
