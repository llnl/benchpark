#Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from .allocation import Allocation
from ramble.modkit import *


class Mpibind(Allocation, BasicModifier):
    """Define a modifier for printing the thread/gpu affinity for each mpi rank"""

    name = "mpibind"

    maintainers("knox10")

    _default_mode = "on"

    mode(
        name="off",
        description="Turn off mpibind",
    )

    mode(
        name="on",
        description="Turn on mpibind",
    )

    mode(
        name="v",
        description="Run mpibind in verbose mode",
    )

    mode(
        name="vv",
        description="Run mpibind in very verbose mode",
    )
    #executable_modifier("mpibind")
    env_var_modification(
        "test",
        "v",
        method="append",
        #separator=",",
        modes=["v"],
    )

    modifier_variable(
        "flux",
        default= False,
        modes=["all"],
        description="mpibind on default val",
    )

    modifier_variable(
        "mpibind_flag",
        default="on",
        modes=["on"],
        description="mpibind on default val",
    )

    modifier_variable(
        "mpibind_flag",
        default="off",
        modes=["off"],
        description="mpibind off default val",
    )

    modifier_variable(
        "mpibind_flag",
        default="v",
        modes=["v"],
        description="mpibind v default flag",
    )

    modifier_variable(
        "mpibind_flag",
        default="vv",
        modes=["all"],
        description="mpibind vv default flag",
    )
    
    #variable_modification(
     #   "{mpi_command}",
     #   "{mpi_command} --mpibind=v",
     #   method="set",
     #   modes=["v"],
    #)
    
    def set_mode(self, scheduler, base_string):
        
        handler = {
            "slurm": "--mpibind=",
            "flux": "-o mpibind=",
            "mpi": "--mpibind=",
            "lsf": "--mpibind=",
            "pjm": "--mpibind=",
        }
        mpi_string = handler.get(scheduler)
        if scheduler == "flux":
            flags = {
                "v": "verbose:1",
                "vv": "verbose:2",
                "on": "on",
                "off": "off",
            }
            mpi_end = flags.get(self.expander.expand_var(self._usage_mode)) 
            return f"{base_string} {mpi_string}{mpi_end}"
        else:
            mpi_end = self.expander.expand_var(self._usage_mode) 
            return f"{base_string} {mpi_string}{mpi_end}"

    def inherit_from_application(self, app):
        super().inherit_from_application(app)
        base_string = app.variables.get("mpi_command")
        scheduler = app.variables.get("scheduler")
        handler = {
            "slurm": "--mpibind=",
            "flux": "-o mpibind=",
            "mpi": "--mpibind=",
            "lsf": "--mpibind=",
            "pjm": "--mpibind=",
        }
        
        mpi_string = handler.get(scheduler)
        #app.variables["mpi_command"] = (f"{base_string} {mpi_string}{self.mode}")
        app.variables["mpi_command"] = self.set_mode(scheduler, base_string)


         


'''
    def add_mpibind_flags(self,v):

    	handler = {
            "slurm": "--mpibind=v",
            "flux": "--setopt=mpibind="
            "mpi": "--mpibind=",
            "lsf": "--mpibind=",
            "pjm": "--mpibind=",
        }
	original_string= v.mpi_command
	v.mpi_command = (f" {original_string} {mpibind_string}")

    def mpibind(self, app):

        #result=super().inherit_from_application(app)
        #print(result)


        pre_exec = []
         post_exec = []
        pre_exec.append(
            CommandExecutable(
                f"foo",
                template=[f"--mpibind=v"],
                mpi=True,

            )
        )

        return pre_exec, post_exec
        '''
