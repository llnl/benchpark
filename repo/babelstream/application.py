# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *
from ramble.expander import Expander

class Babelstream(ExecutableApplication):
    """Babelstream benchmark"""
    name = "babelstream"
   
    tags('memorybenchmark', 'microbenchmark', 'memory-benchmark', 'micro-benchmark')

    tags = ['synthetic',
            'large-scale','multi-node','single-node','sub-node',
            'high-memory-bandwidth','regular-memory-access',
            'mpi','c','fortran','openmp']


    executable('execute', '{execute} -n {n} -s {s}', use_mpi=True)

    workload('babelstream', executable='execute')

    workload_variable('execute', default='openmp-stream', description='executable to run', workloads=['babelstream'])
    workload_variable('n', default='10', description='NTIMES', workloads=['babelstream'])
    workload_variable('s', default='10240000', description='STREAM_ARRAY_SIZE', workloads=['babelstream'])

    log_file = os.path.join(Expander.expansion_str('experiment_run_dir'),
                            Expander.expansion_str('experiment_name') + '.out')


    figure_of_merit("Array size",
                    log_file=log_file,
                    fom_regex=r'Array size\s+\:\s+(?P<array_size>[0-9]+)',
                    group_name='array_size',
                    units='elements')

    figure_of_merit("Array memory",
                    log_file=log_file,
                    fom_regex=r'Memory per array\s+\=\s+(?P<array_mem>[0-9]+)\.*[0-9]*',
                    group_name='array_mem',
                    units='MiB')

    figure_of_merit("Total memory",
                    log_file=log_file,
                    fom_regex=r'Total memory required\s+\=\s+(?P<total_mem>[0-9]+\.*[0-9]*)',
                    group_name='total_mem',
                    units='MiB')

    figure_of_merit("Number of iterations per thread",
                    log_file=log_file,
                    fom_regex=r'Each kernel will be executed\s+(?P<n_times>[0-9]+)',
                    group_name='n_times',
                    units='')

    figure_of_merit("Number of threads",
                    log_file=log_file,
                    fom_regex=r'Number of Threads counted\s+\=\s+(?P<n_threads>[0-9]+\.*[0-9]*)',
                    group_name='n_threads',
                    units='')

    for opName in ['Copy', 'Mul', 'Add', 'Triad', 'Dot']:

        opname = opName.lower()

        opregex = (opName + r'\s*' +
                   r'\s+(?P<' + opname + r'_top_rate>[0-9]+\.[0-9]*)' +
                   r'\s+(?P<' + opname + r'_min_time>[0-9]+\.[0-9]*)' +
                   r'\s+(?P<' + opname + r'_max_time>[0-9]+\.[0-9]*)' +
                   r'\s+(?P<' + opname + r'_avg_time>[0-9]+\.[0-9]*)')

        figure_of_merit(opName + ' top rate',
                        log_file=log_file,
                        fom_regex=opregex,
                        group_name=(opname + '_top_rate'),
                        units='MB/s')

        figure_of_merit(opName + ' min time',
                        log_file=log_file,
                        fom_regex=opregex,
                        group_name=(opname + '_min_time'),
                        units='s')

        figure_of_merit(opName + ' max time',
                        log_file=log_file,
                        fom_regex=opregex,
                        group_name=(opname + '_max_time'),
                        units='s')

        figure_of_merit(opName + ' average time',
                        log_file=log_file,
                        fom_regex=opregex,
                        group_name=(opname + '_avg_time'),
                        units='s') 
