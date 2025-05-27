# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.modkit import *


class Hwloc(BasicModifier):
    """Define a modifier for showing the underlying infrastructure topology"""

    name = "hwloc"

    executable_modifier("hwloc")
    
    mode(
        name="on",
        description="Mode for executing lstopo",
    )

    def hwloc(self, executable_name, executable, app_inst=None):
        import os
        from ramble.util.executable import CommandExecutable

        affinity_log_file = f"{{experiment_run_dir}}/affinity.{self._usage_mode}.out"

        pre_exec = []
        post_exec = []
        print(executable, executable_name)
        # if executable.on:
        pre_exec.append(
            CommandExecutable(
                f"lstopo {executable_name}",
                template=["lstopo"],
            )
        )

            # post_exec.append(
            #     CommandExecutable(
            #         f"unload-affinity-{executable_name}",
            #         template=["spack unload affinity"],
            #     )
            # )

            # affinity_parser_dir = os.path.dirname(f"{self._file_path}")

            # post_exec.append(
            #     CommandExecutable(
            #         f"parse-stdout-{executable_name}",
            #         template=[
            #             f"python {affinity_parser_dir}/parse_affinity_log.py {affinity_log_file} {self._usage_mode}"
            #         ],
            #     )
            # )
        return pre_exec, post_exec
