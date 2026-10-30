# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class SandiaMicroBenchmarks(ExecutableApplication):
    """Sandia Micro Benchmarks

    Message rate benchmarks for MPI communication patterns:
    - mpi_overhead: 2-rank overhead measurement
    - msgrate_9pt: 9-point stencil (8 peers) using pre-post pattern
    - msgrate_27pt: 27-point stencil (26 peers) using pre-post pattern
    - rma_mt: RMA multi-threaded test
    """
    name = "Sandia Micro Benchmarks"

    # Tags for benchmark categorization
    tags = ("mpi", "communication", "microbenchmark")

    # MPI overhead benchmark (2 ranks)
    executable('mpi_overhead_exe', 'mpi_overhead', use_mpi=True)

    # msgrate for 9-point stencil (8 peers)
    # Use -o for machine-readable output, -n for ppn
    executable(
        'msgrate_9pt_exe',
        'msgrate -n {ppn} -p {peers} -s {message_size} -c {cache_size} -o',
        use_mpi=True
    )

    # msgrate for 27-point stencil (26 peers)
    executable(
        'msgrate_27pt_exe',
        'msgrate -n {ppn} -p {peers} -s {message_size} -c {cache_size} -o',
        use_mpi=True
    )

    # RMA multi-threaded test
    executable(
        'rma_mt_exe',
        'msgrate -n {ppn} -p {peers} -s {message_size} -c {cache_size} -o',
        use_mpi=True
    )

    # Workload definitions
    workload('mpi_overhead', executables=['mpi_overhead_exe'])
    workload('msgrate_9pt', executables=['msgrate_9pt_exe'])
    workload('msgrate_27pt', executables=['msgrate_27pt_exe'])
    workload('rma_mt', executables=['rma_mt_exe'])

    # Workload variables
    workload_variable(
        'ppn',
        default='1',
        description='Number of MPI processes per node',
        workloads=['msgrate_9pt', 'msgrate_27pt', 'rma_mt']
    )

    workload_variable(
        'peers',
        default='8',
        description='Number of communication peers (8 for 9-pt, 26 for 27-pt stencil)',
        workloads=['msgrate_9pt', 'msgrate_27pt', 'rma_mt']
    )

    workload_variable(
        'message_size',
        default='1024',
        description='Message size in bytes',
        workloads=['msgrate_9pt', 'msgrate_27pt', 'rma_mt']
    )

    workload_variable(
        'cache_size',
        default='16777216',  # 16 MB default (2x typical L3 cache)
        description='Cache size in bytes for cache clearing',
        workloads=['msgrate_9pt', 'msgrate_27pt', 'rma_mt']
    )

    # Figures of merit for mpi_overhead workload
    figure_of_merit(
        'overhead',
        log_file='{experiment_run_dir}/{experiment_name}.out',
        fom_regex=r'(?:[0-9]+\.?[0-9]* +){4}(?P<fom>[0-9]+\.[0-9]*)',
        group_name='fom',
        units='%',
        workloads=['mpi_overhead']
    )

    # Figures of merit for msgrate workloads
    # With -o flag, output format is machine-readable CSV-like
    # Format: jobsize,npeers,niters,nmsgs,nbytes,cachesz,ppn,single_dir,pair_based,pre_post,all_start

    figure_of_merit(
        'msgrate_single_direction',
        log_file='{experiment_run_dir}/{experiment_name}.out',
        fom_regex=r'single direction:\s+(?P<fom>[0-9]+\.?[0-9]*)',
        group_name='fom',
        units='msgs/sec',
        workloads=['msgrate_9pt', 'msgrate_27pt', 'rma_mt']
    )

    figure_of_merit(
        'msgrate_pair_based',
        log_file='{experiment_run_dir}/{experiment_name}.out',
        fom_regex=r'pair-based:\s+(?P<fom>[0-9]+\.?[0-9]*)',
        group_name='fom',
        units='msgs/sec',
        workloads=['msgrate_9pt', 'msgrate_27pt', 'rma_mt']
    )

    figure_of_merit(
        'msgrate_pre_post',
        log_file='{experiment_run_dir}/{experiment_name}.out',
        fom_regex=r'pre-post:\s+(?P<fom>[0-9]+\.?[0-9]*)',
        group_name='fom',
        units='msgs/sec',
        workloads=['msgrate_9pt', 'msgrate_27pt', 'rma_mt']
    )

    figure_of_merit(
        'msgrate_all_start',
        log_file='{experiment_run_dir}/{experiment_name}.out',
        fom_regex=r'all-start:\s+(?P<fom>[0-9]+\.?[0-9]*)',
        group_name='fom',
        units='msgs/sec',
        workloads=['msgrate_9pt', 'msgrate_27pt', 'rma_mt']
    )

    # Success criteria: ensure the benchmark completed
    success_criteria(
        'completed',
        mode='string',
        match=r'(pre-post:|all-start:)',
        file='{experiment_run_dir}/{experiment_name}.out'
    )
