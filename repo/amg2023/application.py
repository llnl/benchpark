# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Amg2023(ExecutableApplication):
    """AMG2023 benchmark"""
    name = "amg2023"

    tags = ['asc','engineering','hypre','solver','sparse-linear-algebra',
            'large-scale','multi-node','single-node','sub-node',
            'high-branching','high-memory-bandwidth','large-memory-footprint',
            'regular-memory-access','irregular-memory-access','mixed-precision',
            'mpi','network-latency-bound','network-collectives','block-structured-grid',
            'c']

    executable('p1', 'amg' +
                     ' -P {px} {py} {pz}' +
                     ' -n {nx} {ny} {nz}' +
                     ' -problem 1'        +
                     ' -dev_pool_size {pool}' +
                     ' -keepT', use_mpi=True)

    executable('p2', 'amg' +
                     ' -P {px} {py} {pz}' +
                     ' -n {nx} {ny} {nz}' +
                     ' -dev_pool_size {pool}' +
                     ' -problem 2'        +
                     ' -keepT', use_mpi=True)

    workload('problem1', executables=['p1'])
    workload('problem2', executables=['p2'])

    workload_variable('px', default='2',
                      description='px',
                      workloads=['problem1', 'problem2'])
    workload_variable('py', default='2',
                      description='py',
                      workloads=['problem1', 'problem2'])
    workload_variable('pz', default='2',
                      description='pz',
                      workloads=['problem1', 'problem2'])
    workload_variable('nx', default='220',
                      description='nx',
                      workloads=['problem1', 'problem2'])
    workload_variable('ny', default='220',
                      description='ny',
                      workloads=['problem1', 'problem2'])
    workload_variable('nz', default='220',
                      description='nz',
                      workloads=['problem1', 'problem2'])
    workload_variable('pool', default='4',
                      description='Device pool size in GB',
                      workloads=['problem1', 'problem2'])

    figure_of_merit('Figure of Merit (FOM)', log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'Figure of Merit \(FOM\):\s+(?P<fom>[0-9]+\.[0-9]*(e^[0-9]*)?)', group_name='fom', units='')

    #TODO: Fix the FOM success_criteria(...)
    success_criteria('pass', mode='string', match=r'Figure of Merit \(FOM\)', file='{experiment_run_dir}/{experiment_name}.out')

