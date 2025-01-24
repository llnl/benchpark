# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from benchpark.directives import variant
from benchpark.system import System


class Fugaku(System):

    variant(
        "compiler",
        default="clang",
        values=("clang", "gcc", "fj"),
        description="Which compiler to use",
    )

    def initialize(self):
        super().initialize()

        self.scheduler = "pjm"
        self.sys_cores_per_node = "48"
        self.sys_mem_per_node = "32"

    def generate_description(self, output_dir):
        super().generate_description(output_dir)

        sw_description = pathlib.Path(output_dir) / "software.yaml"

        with open(sw_description, "w") as f:
            f.write(self.sw_description())

    def external_pkg_configs(self):
        externals = Fugaku.resource_location / "externals"

        # Doesn't look like we need to switch MPI based on compiler from old definition, verify this
        selections = [externals / "base" / "00-packages.yaml"]

        return selections

    def compiler_configs(self):
        compilers = Fugaku.resource_location / "compilers"

        compiler = self.spec.variants["compiler"][0]

        selections = []

        if compiler == "clang":
            selections.append(compilers / "clang" / "00-clang-17-compilers.yaml")
        elif compiler == "gcc":
            selections.append(compilers / "gcc" / "00-gcc-13-compilers.yaml")
        elif compiler == "fj":
            selections.append(compilers / "fj" / "00-fj-4-compilers.yaml")

        return selections

    def system_specific_variables(self):
        return {
            "extra_cmd_opts": """|
    -std-proc fjmpioutdir/bmexe""",
            "extra_batch_opts": '''|
    -x PJM_LLIO_GFSCACHE="/vol0002:/vol0003:/vol0004:/vol0005:/vol0006"''',
            "post_exec_cmds": """|
    for F in $(ls -1v fjmpioutdir/bmexe.*); do cat $F >> {log_file}; done""",
        }

    def sw_description(self):
        return f"""\
software:
  packages:
    default-compiler:
      pkg_spec: "{self.spec.variants["compiler"][0]}"
    default-mpi:
      pkg_spec: fujitsu-mpi
    compiler-clang:
      pkg_spec: clang
    compiler-fj:
      pkg_spec: fj
    compiler-gcc:
      pkg_spec: gcc
    blas:
      pkg_spec: fujitsu-ssl2
    lapack:
      pkg_spec: fujitsu-ssl2
"""
