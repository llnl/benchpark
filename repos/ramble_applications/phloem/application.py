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
    executable('mpiBench_bundled', 'mpiBench {bundled_test_types} -e {max_msgsize}', use_mpi=True)
    executable('mpiGraph', 'mpiGraph', use_mpi=True)
    executable('com', 'com {test_type} -e {max_msgsize}', use_mpi=True)
    executable('com_bundled', 'com -w {bundled_com_tests} -e {max_msgsize}', use_mpi=True)

    # Define workloads - workload names use underscores instead of spaces
    # sqmr workload (no test type)
    workload('sqmr', executables=['sqmr'])

    # Bundled mpiBench workload (for multiple tests)
    workload('mpiBench_bundled', executables=['mpiBench_bundled'])

    # Bundled com workload (for multiple tests)
    workload('com_bundled', executables=['com_bundled'])

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
                      workloads=mpibench_workloads + com_workloads + ['mpiBench_bundled', 'com_bundled'])

    # Bundled test types variable for running multiple mpiBench tests together
    workload_variable('bundled_test_types', default='',
                      description='Space-separated list of test types for bundled execution',
                      workloads=['mpiBench_bundled'])

    # Bundled test types variable for running multiple com tests together (comma-separated)
    workload_variable('bundled_com_tests', default='',
                      description='Comma-separated list of test types for bundled execution',
                      workloads=['com_bundled'])

    # Define figure of merit patterns for different test types

    # ========== mpiBench FOMs (OSU-style output format) ==========
    # Capture mpiBench summary statistics from table format
    # Format: #bytes  #repetitions  t_min[usec]  t_max[usec]  t_avg[usec]  Mbytes/sec
    figure_of_merit('mpiBench_t_min',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r't_min\[usec\]\s*[=:]?\s*(?P<mpib_t_min>[0-9]+\.?[0-9]*)',
                    group_name='mpib_t_min', units='usec')

    figure_of_merit('mpiBench_t_avg',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r't_avg\[usec\]\s*[=:]?\s*(?P<mpib_t_avg>[0-9]+\.?[0-9]*)',
                    group_name='mpib_t_avg', units='usec')

    figure_of_merit('mpiBench_t_max',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r't_max\[usec\]\s*[=:]?\s*(?P<mpib_t_max>[0-9]+\.?[0-9]*)',
                    group_name='mpib_t_max', units='usec')

    figure_of_merit('mpiBench_bandwidth',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'Mbytes/sec\s+(?P<mpib_bw>[0-9]+\.?[0-9]*)',
                    group_name='mpib_bw', units='MB/s')

    # ========== COM FOMs (Phloem com benchmark format) ==========
    # COM summary lines format: "# Summary  :  min/mean/max =  X.XXX / Y.YYY / Z.ZZZ"
    # Bidirectional Test Results (bandwidth)
    figure_of_merit('com_Bidirectional_min',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#Bidirectional[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*(?P<bidir_min>[0-9]+\.?[0-9]*)',
                    group_name='bidir_min', units='MB/s')

    figure_of_merit('com_Bidirectional_mean',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#Bidirectional[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*[0-9]+\.?[0-9]*\s*/\s*(?P<bidir_mean>[0-9]+\.?[0-9]*)',
                    group_name='bidir_mean', units='MB/s')

    figure_of_merit('com_Bidirectional_max',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#Bidirectional[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*[0-9]+\.?[0-9]*\s*/\s*[0-9]+\.?[0-9]*\s*/\s*(?P<bidir_max>[0-9]+\.?[0-9]*)',
                    group_name='bidir_max', units='MB/s')

    # Latency Test Results
    figure_of_merit('com_Latency_min',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#Latency[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*(?P<lat_min>[0-9]+\.?[0-9]*)',
                    group_name='lat_min', units='usec')

    figure_of_merit('com_Latency_mean',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#Latency[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*[0-9]+\.?[0-9]*\s*/\s*(?P<lat_mean>[0-9]+\.?[0-9]*)',
                    group_name='lat_mean', units='usec')

    figure_of_merit('com_Latency_max',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#Latency[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*[0-9]+\.?[0-9]*\s*/\s*[0-9]+\.?[0-9]*\s*/\s*(?P<lat_max>[0-9]+\.?[0-9]*)',
                    group_name='lat_max', units='usec')

    # BidirAsync Test Results
    figure_of_merit('com_BidirAsync_min',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#BidirAsync[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*(?P<bidirasync_min>[0-9]+\.?[0-9]*)',
                    group_name='bidirasync_min', units='MB/s')

    figure_of_merit('com_BidirAsync_mean',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#BidirAsync[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*[0-9]+\.?[0-9]*\s*/\s*(?P<bidirasync_mean>[0-9]+\.?[0-9]*)',
                    group_name='bidirasync_mean', units='MB/s')

    figure_of_merit('com_BidirAsync_max',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#BidirAsync[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*[0-9]+\.?[0-9]*\s*/\s*[0-9]+\.?[0-9]*\s*/\s*(?P<bidirasync_max>[0-9]+\.?[0-9]*)',
                    group_name='bidirasync_max', units='MB/s')

    # Unidirectional Test Results
    figure_of_merit('com_Unidirectional_min',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#Unidirectional[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*(?P<unidir_min>[0-9]+\.?[0-9]*)',
                    group_name='unidir_min', units='MB/s')

    figure_of_merit('com_Unidirectional_mean',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#Unidirectional[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*[0-9]+\.?[0-9]*\s*/\s*(?P<unidir_mean>[0-9]+\.?[0-9]*)',
                    group_name='unidir_mean', units='MB/s')

    figure_of_merit('com_Unidirectional_max',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#Unidirectional[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*[0-9]+\.?[0-9]*\s*/\s*[0-9]+\.?[0-9]*\s*/\s*(?P<unidir_max>[0-9]+\.?[0-9]*)',
                    group_name='unidir_max', units='MB/s')

    # UnidirAsync Test Results
    figure_of_merit('com_UnidirAsync_min',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#UnidirAsync[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*(?P<unidirasync_min>[0-9]+\.?[0-9]*)',
                    group_name='unidirasync_min', units='MB/s')

    figure_of_merit('com_UnidirAsync_mean',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#UnidirAsync[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*[0-9]+\.?[0-9]*\s*/\s*(?P<unidirasync_mean>[0-9]+\.?[0-9]*)',
                    group_name='unidirasync_mean', units='MB/s')

    figure_of_merit('com_UnidirAsync_max',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'#UnidirAsync[^\n]*\n(?:.*\n)*?# Summary\s*:\s*min/mean/max\s*=\s*[0-9]+\.?[0-9]*\s*/\s*[0-9]+\.?[0-9]*\s*/\s*(?P<unidirasync_max>[0-9]+\.?[0-9]*)',
                    group_name='unidirasync_max', units='MB/s')

    success_criteria('pass', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')
