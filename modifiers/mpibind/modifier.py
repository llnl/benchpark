# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

#from .allocation import *
from ramble.modkit import *
import os
from ramble.util.executable import CommandExecutable


#class Mpibind(Allocation, BasicModifier):
class Mpibind(BasicModifier):
    """Define a modifier for printing the thread/gpu affinity for each mpi rank"""

    name = "mpibind"

    maintainers("knox10")


    mode("standard", description="Standard execution mode for mpibind")
    default_mode("standard")

    executable_modifier("mpibind")

    def mpibind(self, executable_name, executable, app_inst=None):
        pre_exec = []
        post_exec = []
        output_file = f"{{experiment_run_dir}}/{{experiment_name}}.out"
        mpibind_parser_dir = os.path.dirname(f"{self._file_path}")
        post_exec.append(
            CommandExecutable(
                f"parse-stdout-{executable_name}",
                template=[
                    f"python3 {mpibind_parser_dir}/parse_mpibind_output.py {output_file}"
                ],
            )
        )
        return pre_exec, post_exec
