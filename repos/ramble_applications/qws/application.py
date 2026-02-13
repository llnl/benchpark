# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Qws(ExecutableApplication):
    """QWS benchmark for Lattice quantum chromodynamics simulation library for
    Fugaku and computers with wide SIMD
    """
    name = "QWS"

    tags = ['qcd','c++','mpi', 'weak-scaling']

    executable('qws', 'qws.exe' +
                      ' {lx} {ly} {lz} {lt}' +
                      ' {px} {py} {pz} {pt}' +
                      ' {tol_outer} {tol_inner}' +
                      ' {maxiter_plus1_outer} {maxiter_inner}', use_mpi=True)

    workload('qws', executables=['qws'])

    workload_variable('lx', default='32',
                      description='Dimension of the rank-local lattice in X. (Default: 32)',
                      workloads=['qws'])
    workload_variable('ly', default='6',
                      description='Dimension of the rank-local lattice in Y. (Default: 6)',
                      workloads=['qws'])
    workload_variable('lz', default='4',
                      description='Dimension of the rank-local lattice in Z. (Default: 4)',
                      workloads=['qws'])
    workload_variable('lt', default='3',
                      description='Dimension of the rank-local lattice in T. (Default: 3)',
                      workloads=['qws'])
    workload_variable('px', default='1',
                      description='Scale lattice in X dimension by number of ranks. (Default: 1)',
                      workloads=['qws'])
    workload_variable('py', default='1',
                      description='Scale lattice in Y dimension by number of ranks. (Default: 1)',
                      workloads=['qws'])
    workload_variable('pz', default='1',
                      description='Scale lattice in Z dimension by number of ranks. (Default: 1)',
                      workloads=['qws'])
    workload_variable('pt', default='1',
                      description='Scale lattice in T dimension by number of ranks. (Default: 1)',
                      workloads=['qws'])
    workload_variable('tol_outer', default='-1',
                      description='Tolerance of outer DD solver of BiCGStab. (Default: -1)',
                      workloads=['qws'])
    workload_variable('tol_inner', default='-1',
                      description='Tolerance of inner DD solver of BiCGStab. (Default: -1)',
                      workloads=['qws'])
    workload_variable('maxiter_plus1_outer', default='6',
                      description='Maximum iterations of outer DD solver. (Default: 6)',
                      workloads=['qws'])
    workload_variable('maxiter_inner', default='50',
                      description='Maximum iterations of inner DD solver. (Default: 50)',
                      workloads=['qws'])

    figure_of_merit('Figure of Merit (FOM)', log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'etime for so.ler =\s+(?P<fom>[-+]?([0-9]*[.])?[0-9]+([eED][-+]?[0-9]+)?)', group_name='fom', units='')

    success_criteria('pass', mode='string', match=r'print timing', file='{experiment_run_dir}/{experiment_name}.out')
