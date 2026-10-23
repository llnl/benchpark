# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Phloem(ExecutableApplication):
    """Phloem benchmark"""
    name = "phloem"

    tags = ['synthetic',
            'large-scale','multi-node','single-node',
            'c','mpi','network-point-to-point',
            'network-bandwidth-bound','network-latency-bound',
            'network-collectives','network-nonblocking-collectives']

    # Define executables for each benchmark program
    executable('sqmr', 'sqmr --num_cores={num_cores} --num_nbors={num_nbors}', use_mpi=True)
    executable('mpiBench', 'mpiBench {test_type} -e {max_msgsize}', use_mpi=True)
    executable('mpiGraph', 'mpiGraph', use_mpi=True)
    executable('com', 'com {test_type} -e {max_msgsize}', use_mpi=True)

    # Define workloads - workload names use underscores instead of spaces
    # sqmr workload (no test type)
    workload('sqmr', executables=['sqmr'])

    # mpiBench workloads (collective operations)
    workload('mpiBench_Barrier', executables=['mpiBench'])
    workload('mpiBench_Bcast', executables=['mpiBench'])
    workload('mpiBench_Alltoall', executables=['mpiBench'])
    workload('mpiBench_Allgather', executables=['mpiBench'])
    workload('mpiBench_Gather', executables=['mpiBench'])
    workload('mpiBench_Scatter', executables=['mpiBench'])
    workload('mpiBench_Allreduce', executables=['mpiBench'])
    workload('mpiBench_Reduce', executables=['mpiBench'])
    workload('mpiBench_Alltoallv', executables=['mpiBench'])
    workload('mpiBench_Allgatherv', executables=['mpiBench'])
    workload('mpiBench_Gatherv', executables=['mpiBench'])

    # mpiBench non-blocking workloads
    workload('mpiBench_Ibcast', executables=['mpiBench'])
    workload('mpiBench_Ialltoall', executables=['mpiBench'])
    workload('mpiBench_Iallgather', executables=['mpiBench'])
    workload('mpiBench_Igather', executables=['mpiBench'])
    workload('mpiBench_Iscatter', executables=['mpiBench'])
    workload('mpiBench_Iallreduce', executables=['mpiBench'])
    workload('mpiBench_Ireduce', executables=['mpiBench'])
    workload('mpiBench_Ialltoallv', executables=['mpiBench'])
    workload('mpiBench_Iallgatherv', executables=['mpiBench'])
    workload('mpiBench_Igatherv', executables=['mpiBench'])

    # com workloads (point-to-point communication patterns)
    workload('com_Latency', executables=['com'])
    workload('com_Bidirectional', executables=['com'])
    workload('com_BidirAsync', executables=['com'])
    workload('com_Unidirectional', executables=['com'])
    workload('com_UnidirAsync', executables=['com'])

    # mpiGraph workload (no test type)
    workload('mpiGraph', executables=['mpiGraph'])

    # Workload variables for sqmr
    # Formula: total_ranks = num_cores * (num_nbors + 1)
    # For 4 ranks: 2 cores * (1 neighbor + 1) = 4 ranks
    workload_variable('num_cores', default='2',
                      description='Number of MPI ranks on the core node, correlates to number of cores on one compute node.',
                      workloads=['sqmr'])

    workload_variable('num_nbors', default='1',
                      description='Number of distinct neighbors to each rank on the core node.',
                      workloads=['sqmr'])

    # Workload variables for test type - specify explicitly for each workload
    # mpiBench workloads
    workload_variable('test_type', default='Barrier', description='Test type', workloads=['mpiBench_Barrier'])
    workload_variable('test_type', default='Bcast', description='Test type', workloads=['mpiBench_Bcast'])
    workload_variable('test_type', default='Alltoall', description='Test type', workloads=['mpiBench_Alltoall'])
    workload_variable('test_type', default='Allgather', description='Test type', workloads=['mpiBench_Allgather'])
    workload_variable('test_type', default='Gather', description='Test type', workloads=['mpiBench_Gather'])
    workload_variable('test_type', default='Scatter', description='Test type', workloads=['mpiBench_Scatter'])
    workload_variable('test_type', default='Allreduce', description='Test type', workloads=['mpiBench_Allreduce'])
    workload_variable('test_type', default='Reduce', description='Test type', workloads=['mpiBench_Reduce'])
    workload_variable('test_type', default='Alltoallv', description='Test type', workloads=['mpiBench_Alltoallv'])
    workload_variable('test_type', default='Allgatherv', description='Test type', workloads=['mpiBench_Allgatherv'])
    workload_variable('test_type', default='Gatherv', description='Test type', workloads=['mpiBench_Gatherv'])
    workload_variable('test_type', default='Ibcast', description='Test type', workloads=['mpiBench_Ibcast'])
    workload_variable('test_type', default='Ialltoall', description='Test type', workloads=['mpiBench_Ialltoall'])
    workload_variable('test_type', default='Iallgather', description='Test type', workloads=['mpiBench_Iallgather'])
    workload_variable('test_type', default='Igather', description='Test type', workloads=['mpiBench_Igather'])
    workload_variable('test_type', default='Iscatter', description='Test type', workloads=['mpiBench_Iscatter'])
    workload_variable('test_type', default='Iallreduce', description='Test type', workloads=['mpiBench_Iallreduce'])
    workload_variable('test_type', default='Ireduce', description='Test type', workloads=['mpiBench_Ireduce'])
    workload_variable('test_type', default='Ialltoallv', description='Test type', workloads=['mpiBench_Ialltoallv'])
    workload_variable('test_type', default='Iallgatherv', description='Test type', workloads=['mpiBench_Iallgatherv'])
    workload_variable('test_type', default='Igatherv', description='Test type', workloads=['mpiBench_Igatherv'])

    # com workloads
    workload_variable('test_type', default='Latency', description='Test type', workloads=['com_Latency'])
    workload_variable('test_type', default='Bidirectional', description='Test type', workloads=['com_Bidirectional'])
    workload_variable('test_type', default='BidirAsync', description='Test type', workloads=['com_BidirAsync'])
    workload_variable('test_type', default='Unidirectional', description='Test type', workloads=['com_Unidirectional'])
    workload_variable('test_type', default='UnidirAsync', description='Test type', workloads=['com_UnidirAsync'])

    # Maximum message size for mpiBench and com workloads (in bytes)
    # Default: 33554432 bytes = 32 MB
    # Can be overridden via experiment configuration
    mpibench_workloads = ['mpiBench_Barrier', 'mpiBench_Bcast', 'mpiBench_Alltoall',
                          'mpiBench_Allgather', 'mpiBench_Gather', 'mpiBench_Scatter',
                          'mpiBench_Allreduce', 'mpiBench_Reduce', 'mpiBench_Alltoallv',
                          'mpiBench_Allgatherv', 'mpiBench_Gatherv', 'mpiBench_Ibcast',
                          'mpiBench_Ialltoall', 'mpiBench_Iallgather', 'mpiBench_Igather',
                          'mpiBench_Iscatter', 'mpiBench_Iallreduce', 'mpiBench_Ireduce',
                          'mpiBench_Ialltoallv', 'mpiBench_Iallgatherv', 'mpiBench_Igatherv']

    com_workloads = ['com_Latency', 'com_Bidirectional', 'com_BidirAsync',
                     'com_Unidirectional', 'com_UnidirAsync']

    workload_variable('max_msgsize', default='33554432',
                      description='Maximum message size in bytes (default: 32 MB)',
                      workloads=mpibench_workloads + com_workloads)

    # Define figure of merit patterns for different test types
    figure_of_merit('Latency',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'(?P<latency>[0-9]+\.?[0-9]*)\s+(?:us|usec|microseconds)',
                    group_name='latency', units='usec')

    figure_of_merit('Bandwidth',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'(?P<bandwidth>[0-9]+\.?[0-9]*)\s+(?:MB/s|MBps)',
                    group_name='bandwidth', units='MB/s')

    figure_of_merit('Time',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'(?P<time>[0-9]+\.?[0-9]*)\s+(?:ms|msec|milliseconds)',
                    group_name='time', units='ms')

    success_criteria('pass', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')
