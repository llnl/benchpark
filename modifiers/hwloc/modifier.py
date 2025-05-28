# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.modkit import *


class Hwloc(BasicModifier):
    """Define a modifier for showing the underlying infrastructure topology"""

    name = "hwloc"
    
    mode(
        name="on",
        description="Mode for executing lstopo",
    )

    executable_modifier("hwloc")

    def hwloc(self, executable_name, executable, app_inst=None):
        import os
        from ramble.util.executable import CommandExecutable

        
        hwloc_output_file = f"{{experiment_run_dir}}/hwloc.out"

        pre_exec = []
        post_exec = []

        pre_exec.append(
            CommandExecutable(
                f"get-underlying-topology",
                template=["lstopo --whole-system --io --verbose"],
                redirect=hwloc_output_file
            )
        )

        hwloc_parser_dir = os.path.dirname(f"{self._file_path}")

        post_exec.append(
            CommandExecutable(
                f"parse-lstopo-output",
                template=[
                        f"python {hwloc_parser_dir}/parse_hwloc_output.py {hwloc_output_file} {self._usage_mode}"
                    ],
            )
        )

        return pre_exec, post_exec
