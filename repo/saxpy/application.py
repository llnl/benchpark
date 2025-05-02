# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Saxpy(ExecutableApplication):
    """saxpy benchmark"""
    name = "saxpy"

    tags = ['synthetic','single-node','high-memory-bandwidth',
            'regular-memory-access',
            'c++']

    executable('p', 'saxpy -n {n}', use_mpi=True)

    workload('problem', executables=['p'])

    workload_variable('n', default='1024', description='problem size', workloads=['problem'])

    figure_of_merit('Kernel {num} size', fom_regex=r'Kernel done \((?P<num>[0-9]+)\): (?P<size>[0-9]+)', group_name='size', units='')
    figure_of_merit("success", fom_regex=r'(?P<done>Kernel done)', group_name='done', units='')

    success_criteria('pass', mode='string', match=r'Kernel done', file='{experiment_run_dir}/{experiment_name}.out')
