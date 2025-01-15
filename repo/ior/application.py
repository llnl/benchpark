# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Ior(ExecutableApplication):
    """Ior benchmark"""
    name = "ior"

    executable('p', 'ior -w -F'+
            ' -b {b}' +
            ' -t {t}' + 
            ' -a {a}' +
            ' {o}'
            , use_mpi=True)

    workload('ior', executables=['p'])

    workload_variable('a', default='POSIX',
        description='api',
        workloads=['ior'])

    workload_variable('b', default='16m',
        description='blockSize -- contiguous bytes to write per task  (e.g.: 8, 4k, 2m, 1g)',
        workloads=['ior'])

    workload_variable('t', default='1m',
        description='transferSize -- size of transfer in bytes (e.g.: 8, 4k, 2m, 1g)',
        workloads=['ior'])

    workload_variable('N', default='1',
        description='numTasks -- number of tasks that are participating in the test (overrides MPI)',
        workloads=['ior'])

    workload_variable('o', default='',
        description='directory to read/write to',
        workloads=['ior'])

    figure_of_merit('Mean write',
        log_file='{experiment_run_dir}/{experiment_name}.out',
        fom_regex=r'write\s+\d*\.\d*\s+\d*\.\d*\s+(?P<fom>[0-9]+\.[0-9]*)',
        group_name='fom', units='MiB')

    figure_of_merit('Std Deviation',
        log_file='{experiment_run_dir}/{experiment_name}.out',
        fom_regex=r'write\s+\d*\.\d*\s+\d*\.\d*\s+\d*\.\d*\s+(?P<fom>[0-9]+\.[0-9]*)',
        group_name='fom', units='')

    success_criteria('pass', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')
