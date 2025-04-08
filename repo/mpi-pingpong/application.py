# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class MpiPingpong(ExecutableApplication):
    name = "mpi-pingpong"

    tags = ['single-node']

    executable("pingpong", "pingpong -i {iterations} -m {msg_size}", use_mpi=True)

    workload("run", executables=["pingpong"])
