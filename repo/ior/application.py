# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Ior(ExecutableApplication):
    """Ior benchmark"""

    name = "ior"

    tags = ["synthetic", "i-o", "large-scale", "mpi", "c"]

    params = " -b {b}" + " -t {t}" + " -i {i}" + " -o {o}"
    common_args = ' -Cge -vv {test_file_mode}'

    # MPIIO
    common_mpiio = "ior -a MPIIO -m -c" + common_args + params
    executable("mpiio-write", common_mpiio + " -w", use_mpi=True)
    executable("mpiio-read", common_mpiio + " -E -r", use_mpi=True)

    # POSIX
    common_posix = "ior -a POSIX" + common_args + params
    executable(
        "posix-write", common_posix + " -w --posix.odirect -k", use_mpi=True
    )
    executable("posix-read", common_posix + " -E -r", use_mpi=True)

    # No GTL
    executable("disable_gtl", "export MPICH_GPU_SUPPORT_ENABLED=0", use_mpi=False)

    workload("mpiio-write", executables=["disable_gtl", "mpiio-write"])
    workload("mpiio-read", executables=["disable_gtl", "mpiio-read"])
    workload("posix-write", executables=["disable_gtl", "posix-write"])
    workload("posix-read", executables=["disable_gtl", "posix-read"])

    workload_variable(
        "b",
        default="16m",
        description="blockSize -- contiguous bytes to write per task  (e.g.: 8, 4k, 2m, 1g)",
        workloads=["mpiio-write", "mpiio-read", "posix-write", "posix-read"],
    )

    workload_variable(
        "i",
        default=10,
        description="repetitions -- number of repetitions of test",
        workloads=["mpiio-write", "mpiio-read", "posix-write", "posix-read"],
    )

    workload_variable(
        "t",
        default="1m",
        description="transferSize -- size of transfer in bytes (e.g.: 8, 4k, 2m, 1g)",
        workloads=["mpiio-write", "mpiio-read", "posix-write", "posix-read"],
    )

    # TODO: Simplify FOMs

    figure_of_merit(
        "Mean write OPs",
        log_file="{experiment_run_dir}/{experiment_name}.out",
        # Skip the first 6 numbers in row starting with "write"
        fom_regex=r"write\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)?)",
        group_name="fom",
        units="OPs",
    )
    figure_of_merit(
        "Mean read OPs",
        log_file="{experiment_run_dir}/{experiment_name}.out",
        # Skip the first 6 numbers in row starting with "read"
        fom_regex=r"read\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)?)",
        group_name="fom",
        units="OPs",
    )
    figure_of_merit(
        "Mean write",
        log_file="{experiment_run_dir}/{experiment_name}.out",
        # Skip the first 2 numbers in row starting with "write"
        fom_regex=r"write\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)?)",
        group_name="fom",
        units="MiB/sec",
    )
    figure_of_merit(
        "Mean read",
        log_file="{experiment_run_dir}/{experiment_name}.out",
        # Skip the first 2 numbers in row starting with "read"
        fom_regex=r"read\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)?)",
        group_name="fom",
        units="MiB/sec",
    )
    # Pass if output in file
    success_criteria(
        "pass",
        mode="string",
        match=r".*",
        file="{experiment_run_dir}/{experiment_name}.out",
    )
