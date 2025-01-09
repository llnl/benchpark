# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Gpcnet(ExecutableApplication):
    """GPCNet benchmark"""
    name = "GPCNet"

    executable('p1', 'network_test', use_mpi=True)
    executable('p2', 'network_load_test', use_mpi=True)
    workload('network_test', executables=['p1'])
    workload('network_load_test', executables=['p2'])

    figure_of_merit('Avg Multiple Allreduce',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'\|\s+Multiple Allreduce \([0-9]* B\)\s+\|\s+(?P<fom>[0-9]+\.[0-9]*)',
                    group_name='fom', units='MiB/sec')
    figure_of_merit('Avg RR Two-sided Lat',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'\|\s+RR Two-sided Lat \([0-9]* B\)\s+\|\s+(?P<fom>[0-9]+\.[0-9]*)',
                    group_name='fom', units='MiB/sec')
    figure_of_merit('Avg RR Get Lat',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'\|\s+RR Get Lat \([0-9]* B\)\s+\|\s+(?P<fom>[0-9]+\.[0-9]*)',
                    group_name='fom', units='MiB/sec')
    success_criteria('pass', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')
