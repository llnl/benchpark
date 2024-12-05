# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from benchpark.directives import variant
from benchpark.system import System

id_to_resources = {
    "ruby": {
        "sys_cores_per_node": 56,
    },
    "magma": {
        "sys_cores_per_node": 96,
    },
    "dane": {
        "sys_cores_per_node": 112,
    },
}


class LlnlCluster(System):

    variant(
        "cluster",
        default="ruby",
        values=("ruby", "magma", "dane"),
        description="Which cluster to run on",
    )

    variant(
        "compiler",
        default="gcc",
        values=("gcc", "intel"),
        description="Which compiler to use",
    )

    variant(
        "lapack",
        default="intel-oneapi-mkl",
        description="Which lapack to use",
    )

    variant(
        "blas",
        default="intel-oneapi-mkl",
        description="Which blas to use",
    )

    def initialize(self):
        super().initialize()

        self.scheduler = "slurm"
        attrs = id_to_resources.get(self.spec.variants["cluster"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def generate_description(self, output_dir):
        super().generate_description(output_dir)

        sw_description = pathlib.Path(output_dir) / "software.yaml"

        with open(sw_description, "w") as f:
            f.write(self.sw_description())

    def external_pkg_configs(self):
        externals = LlnlCluster.resource_location / "externals"

        selections = [externals / "base" / "00-packages.yaml"]

        if self.spec.satisfies("compiler=gcc"):
            selections.append(externals / "mpi" / "00-gcc-packages.yaml")
        elif self.spec.satisfies("compiler=intel"):
            selections.append(externals / "mpi" / "01-intel-packages.yaml")

        return selections

    def compiler_configs(self):
        compilers = LlnlCluster.resource_location / "compilers"

        selections = []
        if self.spec.satisfies("compiler=gcc"):
            selections.append(compilers / "gcc" / "00-gcc-12-compilers.yaml")
        elif self.spec.satisfies("compiler=intel"):
            selections.append(compilers / "intel" / "00-intel-2021-6-0-compilers.yaml")

        return selections

    def sw_description(self):
        """This is somewhat vestigial, and maybe deleted later. The experiments
        will fail if these variables are not defined though, so for now
        they are still generated (but with more-generic values).
        """
        return f"""\
software:
  packages:
    default-compiler:
      pkg_spec: gcc
    default-mpi:
      pkg_spec: mvapich2
    default-lapack:
      pkg_spec: {self.spec.variants["lapack"][0]}
    default-blas:
      pkg_spec: {self.spec.variants["blas"][0]}
    compiler-gcc:
      pkg_spec: gcc
    compiler-intel:
      pkg_spec: intel
    blas:
      pkg_spec: intel-oneapi-mkl
    lapack:
      pkg_spec: intel-oneapi-mkl
    mpi-gcc:
      pkg_spec: mvapich2
    mpi-intel:
      pkg_spec: mvapich2
"""
