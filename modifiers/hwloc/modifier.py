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

        
        hwloc_log_file = f"{{experiment_run_dir}}/hwloc.{self._usage_mode}.out"

        pre_exec = []
        post_exec = []

        pre_exec.append(
            CommandExecutable(
                f"get-underlying-topology",
                template=["lstopo"],
                redirect=hwloc_log_file
            )
        )

        return pre_exec, post_exec
