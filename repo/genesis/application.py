# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.appkit import *

import sys

class Genesis(SpackApplication):
    """GENESIS package contains two MD programs (atdyn and spdyn), trajectory
    analysis programs, and other useful tools. GENESIS (GENeralized-Ensemble
    SImulation System) has been developed mainly by Sugita group in RIKEN-CCS.
    """
    name = "GENESIS"

    tags = ['molecular-dynamics','mpi', 'openmp', 'cuda']

    executable('chdir', 'cd $(dirname {input})', use_mpi=False)
    executable('genesis', 'spdyn {input}', use_mpi=True)

    input_file('benchmark-2020',
               url='https://www.r-ccs.riken.jp/labs/cbrt/wp-content/uploads/2020/12/benchmark_mkl_ver4_nocrowding.tar.gz',
               sha256='2ca8b2d4974dc0be0a42064392f1d5c603c64ffa9adc1f3bcf7c146a3bbf5bdb',
               description='Benchmark set for GENESIS 2.0 beta / 1.6 on FUGAKU')
    input_file('tests-2.1.1',
               url='https://www.r-ccs.riken.jp/labs/cbrt/wp-content/uploads/2023/09/tests-2.1.1.tar.bz2',
               sha256='f24d872beae5e38baa6a591906f78e3438186973c88e4879e4b04a0cca74f83e',
               description='Regression tests are prepared for ATDYN, SPDYN, prst_setup (parallel I/O), and analysis tools to check if these programs work correctly.')

    workload('DHFR', executables=['chdir', 'genesis'], input='benchmark-2020')
    workload('ApoA1', executables=['chdir', 'genesis'], input='benchmark-2020')
    workload('UUN', executables=['chdir', 'genesis'], input='benchmark-2020')
    workload('cryoEM', executables=['chdir', 'genesis'], input='tests-2.1.1')

    workload_variable('input', default='{benchmark-2020}/npt/genesis2.0beta/jac_amber/p{n_ranks}.inp',
                      description='jac_amber/ : DHFR (27,346 atoms), AMBER format, soluble system',
                      workloads=['DHFR'])
    workload_variable('input', default='{benchmark-2020}/npt/genesis2.0beta/apoa1/p{n_ranks}.inp',
                      description='apoa1/ : apoa1 (92,224 atoms), CHARMM format, soluble system',
                      workloads=['ApoA1'])
    workload_variable('input', default='{benchmark-2020}/npt/genesis2.0beta/uun/p{n_ranks}.inp',
                      description='uun/ : uun (216,726 atoms), CHARMM format, membrane+solvent system',
                      workloads=['UUN'])
    workload_variable('input', default='{tests-2.1.1}/regression_test/test_spdyn/cryoEM/All_atom/inp',
                      description='cryoEM/All_atom/ : cryoEM (? atoms), CHARMM format',
                      workloads=['cryoEM'])

    figure_of_merit('Figure of Merit (FOM)', log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'^\s+dynamics\s+=\s+(?P<fom>[-+]?([0-9]*[.])?[0-9]+([eED][-+]?[0-9]+)?)', group_name='fom', units='')

    success_criteria('pass', mode='string', match=r'Figure of Merit \(FOM\)', file='{experiment_run_dir}/{experiment_name}.out')
