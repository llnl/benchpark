# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from benchpark.system import System


class GenericX86(System):
    """This is the generic system class for an x86 system, gcc compiler, mpi.
    It can be easily copied and modified to model other systems."""

    maintainers("slabasan")

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [OpenMPCPUOnlySystem()]

        self.scheduler = "mpi"
        setattr(self, "sys_cores_per_node", 1)

    def compute_software_section(self):
        """This is somewhat vestigial, and maybe deleted later. The experiments
        will fail if these variables are not defined though, so for now
        they are still generated (but with more-generic values).
        """
        return {
            "software": {
                "packages": {
                    "default-compiler": {"pkg_spec": "gcc"},
                    "compiler-gcc": {"pkg_spec": "gcc"},
                    "default-mpi": {"pkg_spec": "openmpi"},
                    "blas": {"pkg_spec": "openblas"},
                    "lapack": {"pkg_spec": "openblas"},
                }
            }
        }
