# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class MpiPingpong(ExecutableApplication):
    name = "mpi-pingpong"

    tags = ['single-node', 'builtin-caliper']


    executable("pingpong", "pingpong -i {iterations} -m {msg_size} -p 0,{partner_rank} -n {n_nodes} -s {sys_cores_per_node}//{sys_sockets_per_node} -c {sys_cores_per_node} -b {experiment_run_dir}/{experiment_name}_metadata.json", use_mpi=True)
    #executable("pingpong1", "pingpong -i {iterations} -m {msg_size} -p 0,56", use_mpi=True)
    #executable("pingpong2", "pingpong -i {iterations} -m {msg_size} -p 0,112", use_mpi=True)

    workload("run", executables=["pingpong"])
