# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from benchpark.system import System


class Genericx86(System):
    """This is the generic system class for an x86 system, gcc compiler, mpi.
    It can be easily copied and modified to model other systems."""

    def initialize(self):
        super().initialize()

        self.scheduler = "mpi"
        setattr(self, "sys_cores_per_node", 1)

    def generate_description(self, output_dir):
        super().generate_description(output_dir)

        sw_description = pathlib.Path(output_dir) / "software.yaml"

        with open(sw_description, "w") as f:
            f.write(self.sw_description())

    def sw_description(self):
        """This is somewhat vestigial, and maybe deleted later. The experiments
        will fail if these variables are not defined though, so for now
        they are still generated (but with more-generic values).
        """
        return """\
software:
  packages:
    default-compiler:
      pkg_spec: gcc
    compiler-gcc:
      pkg_spec: gcc
    default-mpi:
      pkg_spec: openmpi
    zlib-api:
      require: zlib
"""
