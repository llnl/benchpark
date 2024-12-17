# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Smb(ExecutableApplication):
    """Sandia microbenchmarks"""
    name = "Sandia microbenchmarks"

    executable('p1', 'mpi_overhead -v', use_mpi=True)
    executable('p2', 'msgrate -n {ppn}', use_mpi=True)

    workload('mpi_overhead', executables=['p1'])
    workload('msgrate', executables=['p2'])
    workload('rma_mt', executables=['p2'])

    workload_variable('ppn', default='1',
                   description='Number of procs per node',
                   workloads=['msgrate', 'rma_mt'])

    figure_of_merit('single direction',
                   log_file='{experiment_run_dir}/{experiment_name}.out',
                   fom_regex=r'single direction:\s+(?P<fom>[0-9]+\.[0-9]*)',
                  group_name='fom', units='')
    #TODO:fix this FOM. Not sure what's causing it to not detect
    figure_of_merit('overhead',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'(?:[0-9]+\.?[0-9]* +){4}(?P<fom>[0-9]+\.[0-9]*)',
                    #fom_regex=r'avail\(%\)(?:\s|\t)*\n\s*(?:[0-9]+\.*[0-9]*\s*){4}(?P<fom>[0-9]+\.*[0-9]*)',
                   group_name='fom', units='')

    figure_of_merit('pair based',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'pair-based:\s+(?P<fom>[0-9]+\.[0-9]*)',
                   group_name='fom', units='')

    figure_of_merit('pre-post',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'\s*pre-post:\s+(?P<fom>[0-9]+\.[0-9]*)',
                   group_name='fom', units='')

    figure_of_merit('all-start',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'\s*all-start:\s+(?P<fom>[0-9]+\.[0-9]*)',
                   group_name='fom', units='')
    #success_criteria('pass', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')
