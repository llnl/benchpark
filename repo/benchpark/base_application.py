# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0
import sys
from ramble.appkit import *

class benchpark(ExecutableApplication):
  """Define a base benchpark application."""

  name = "benchpark"

  workload_group("standard", workloads=[])
  
  workload_variable('n_resources', default="1",
                    description='How many processes (CPU cores or GPUs) are required',
                    workload_group="standard",
                   )
  workload_variable('process_problem_size', default="1",
                    description='Problem size per process',
                    workload_group="standard",
                   )
  workload_variable('total_problem_size', default="1",
                    description='Total problem size',
                    workload_group="standard",
                   )
