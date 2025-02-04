# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.modkit import *


def set_affinity_mode(mode_name, mode_option, description):
    mode(
        name=mode_name,
        description=description,
    )

    env_var_modification(
        "AFFINITY_MODE",
        mode_option,
        method="set",
        modes=[mode_name],
    )


def append_affinity_mode(mode_name, mode_option, description):
    mode(
        name=mode_name,
        description=description,
    )

    env_var_modification(
        "AFFINITY_MODE",
        mode_option,
        method="append",
        separator="; ",
        modes=[mode_name],
    )


class Affinity(BasicModifier):
    """Define a modifier for printing the thread/gpu affinity for each mpi rank"""

    name = "affinity"

    tags("thread affinity", "gpu affinity")

    maintainers("nhanford")

    _default_mode = "mpi"

    append_affinity_mode(
        mode_name=_default_mode,
        mode_option=f"affinity.{_default_mode}",
        description="Mode for testing thread affinity of each rank in an MPI job",
    )

    set_affinity_mode(
        mode_name="cuda",
        mode_option="affinity.cuda",
        description="Mode for testing NVIDIA GPU affinity of each rank in an MPI job",
    )

    set_affinity_mode(
        mode_name="rocm",
        mode_option="affinity.rocm",
        description="Mode for testing AMD GPU affinity of each rank an MPI job",
    )

    variable_modification(
        "mpi_command", "${AFFINITY_MODE}; ", method="append", modes=["mpi"]
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
