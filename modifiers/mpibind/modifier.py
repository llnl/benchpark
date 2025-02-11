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
    mode(
            name="greedy:0",
        description="Run mpibind in very verbose mode",
    )

    modifier_variable(
        "flux",
        default= False,
        modes=["all"],
        description="mpibind on default val",
    )

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
        app.variables["mpi_command"] = self.set_mode(scheduler, base_string)

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
                "greedy:0": "greedy:0",
            }
            mpi_end = flags.get(self.expander.expand_var(self._usage_mode)) 
            return f"{base_string} {mpi_string}{mpi_end}"
        else:
            mpi_end = self.expander.expand_var(self._usage_mode) 
            return f"{base_string} {mpi_string}{mpi_end}"
