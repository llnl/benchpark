# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *
from ramble.expander import Expander


class Commbench(ExecutableApplication):
    name = "commbench"

    maintainers("arhag23")

    software_spec("commbench", pkg_spec="commbench", package_manager="spack*")

    executable("execute-bench", "CommBench --use {lib} --pattern {pat}", use_mpi=True)
    # executable("execute-test", "mpiexec -n {n_ranks} CommBench --use {lib} --pattern {pat} --validate", use_mpi=True)
    executable("execute-test", "CommBench --use {lib} --pattern {pat} --validate", use_mpi=True)
    # executable("execute-test3", "mpiexec -n {n_ranks} CommBench --use {lib} --pattern {pat} --validate")
    # executable("execute-test4", "mpiexec CommBench --use {lib} --pattern {pat} --validate", use_mpi=True)

    workload("basic", executables=["execute-test"])

    workload_variable("lib", default="mpi", values=["mpi", "ipc_get", "ipc_put", "xccl"], description="Communication library to benchmark", workload="basic")
    workload_variable("pat", default="p2p", values=["p2p", "gather", "scatter", "broadcast", "alltoall", "allgather"], description="Communication pattern", workload="basic")
    # workload_variable("mpi_command", default="mpirun -n {n_ranks}", description="mpi command", workload="basic")
    
    # success_criteria("pass", "string", match="[\s\S.]*PASSED![\s\S.]*")
