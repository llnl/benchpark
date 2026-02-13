# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.modkit import *


class Affinity(BasicModifier):
    """Define a modifier for printing the thread/gpu affinity for each mpi rank"""

    name = "affinity"

    tags("thread affinity", "gpu affinity")

    maintainers("nhanford")

    _default_mode = "mpi"

    mode(
        name="mpi",
        description="Mode for testing thread affinity of each rank in an MPI job",
    )

    mode(
        name="cuda",
        description="Mode for testing NVIDIA GPU affinity of each rank in an MPI job",
    )

    mode(
        name="rocm",
        description="Mode for testing AMD GPU affinity of each rank an MPI job",
    )

    executable_modifier("affinity")

    def affinity(self, executable_name, executable, app_inst=None):
        import os

        from ramble.util.executable import CommandExecutable

        affinity_file = f"{{experiment_run_dir}}/affinity.{self._usage_mode}"
        affinity_log_file = affinity_file + ".out"
        affinity_json_file = affinity_file + ".json"

        pre_exec = []
        post_exec = []

        # attach affinity json data to caliper metadata if caliper is on
        caliper_modifier = any(
            [modifier["name"] == "caliper" for modifier in app_inst.modifiers]
        )
        if caliper_modifier:
            pre_exec.append(
                CommandExecutable(
                    f"modify-caliper-config-{executable_name}",
                    template=[
                        'export CALI_CONFIG="$CALI_CONFIG,metadata(file={})"'.format(
                            affinity_json_file
                        )
                    ],
                )
            )

        if executable.mpi:
            pre_exec.append(
                CommandExecutable(
                    f"load-affinity-{executable_name}",
                    template=["spack load affinity"],
                )
            )

            pre_exec.append(
                CommandExecutable(
                    f"run-affinity-{executable_name}",
                    template=[f"affinity.{self._usage_mode}"],
                    mpi=True,
                    redirect=affinity_log_file,
                )
            )

            affinity_parser_dir = os.path.dirname(f"{self._file_path}")
            pre_exec.append(
                CommandExecutable(
                    f"parse-stdout-{executable_name}",
                    template=[
                        f"python {affinity_parser_dir}/parse_affinity_log.py {affinity_log_file} {self._usage_mode}"
                    ],
                )
            )

            post_exec.append(
                CommandExecutable(
                    f"unload-affinity-{executable_name}",
                    template=["spack unload affinity"],
                )
            )

        return pre_exec, post_exec
