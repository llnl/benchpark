# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.modkit import *


def add_mode(name, description):
    mode(
        name=name,
        description=description,
    )

    variable_modification(
        "mpi_command", f"affinity.{name} ; ", method="append", modes=[name]
    )


class Affinity(BasicModifier):
    """Define a modifier for printing the thread/gpu affinity for each mpi rank"""

    name = "affinity"

    tags("thread affinity", "gpu affinity")

    maintainers("nhanford")

    _default_mode = "mpi"

    add_mode(
        name="mpi",
        description="Mode for testing thread affinity of each rank in an MPI job",
    )

    add_mode(
        name="cuda",
        description="Mode for testing NVIDIA GPU affinity of each rank in an MPI job",
    )

    add_mode(
        name="rocm",
        description="Mode for testing AMD GPU affinity of each rank an MPI job",
    )

    executable_modifier("affinity")

    def affinity(self, executable_name, executable, app_inst=None):
        from ramble.util.executable import CommandExecutable

        pre_exec = []
        post_exec = []
        if executable.mpi:
            pre_exec.append(
                CommandExecutable(
                    f"load-affinity",
                    template=["spack load affinity"],
                )
            )
            post_exec.append(
                CommandExecutable(
                    f"unload-affinity",
                    template=["spack unload affinity"],
                )
            )

        return pre_exec, post_exec
