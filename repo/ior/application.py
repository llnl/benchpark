# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Ior(ExecutableApplication):
    """Ior benchmark"""
    name = "ior"

    tags = ['synthetic','i-o','large-scale','mpi','c']

    executable('p', 'ior -Cge -vv -F -c -w -m'+
            ' -b {b}' +
            ' -t {t}' + 
            ' -a {a}' +
            ' -i {i}' +
            ' -o {o}'
            , use_mpi=True)

    executable('disable_gtl', 'export MPICH_GPU_SUPPORT_ENABLED=0', use_mpi=False)

    workload('ior', executables=['disable_gtl', 'p'])

    workload_variable('a', default='MPIIO',
        description='api',
        workloads=['ior'])

    workload_variable('b', default='16m',
        description='blockSize -- contiguous bytes to write per task  (e.g.: 8, 4k, 2m, 1g)',
        workloads=['ior'])

    workload_variable('i', default=10,
        description='repetitions -- number of repetitions of test',
        workloads=['ior'])

    workload_variable('t', default='1m',
        description='transferSize -- size of transfer in bytes (e.g.: 8, 4k, 2m, 1g)',
        workloads=['ior'])

    workload_variable('N', default='1',
        description='numTasks -- number of tasks that are participating in the test (overrides MPI)',
        workloads=['ior'])
    #TODO: Simplify FOMs
    
    figure_of_merit('Mean write OPs',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    # Skip the first 6 numbers in row starting with "write"
                    fom_regex=r'write\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)?)',
                    group_name='fom', units='OPs')
    figure_of_merit('Mean read OPs',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    # Skip the first 6 numbers in row starting with "read"
                    fom_regex=r'read\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)?)',
                    group_name='fom', units='OPs')
    figure_of_merit('Mean write',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    # Skip the first 2 numbers in row starting with "write"
                    fom_regex=r'write\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)?)',
                    group_name='fom', units='MiB/sec')
    figure_of_merit('Mean read',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    # Skip the first 2 numbers in row starting with "read"
                    fom_regex=r'read\s+[0-9]+\.[0-9]*[0-9]*\s+[0-9]+\.[0-9]*[0-9]*\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)?)',
                    group_name='fom', units='MiB/sec')
    # Pass if output in file
    success_criteria('pass', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')
