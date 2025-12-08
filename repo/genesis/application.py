# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Genesis(ExecutableApplication):
    """GENESIS package contains two MD programs (atdyn and spdyn), trajectory
    analysis programs, and other useful tools. GENESIS (GENeralized-Ensemble
    SImulation System) has been developed mainly by Sugita group in RIKEN-CCS.
    """
    name = "GENESIS"

    tags = ['molecular-dynamics','mpi']

    executable('chdir', 'cd $(dirname {input})', use_mpi=False)
    executable('genesis', 'spdyn {input}', use_mpi=True)

    input_file('benchmark-input',
               url='https://github.com/genesis-release-r-ccs/genesis_benchmark_input/archive/refs/tags/v1.0.0.tar.gz',
               sha256='13a04449f4036e38a640fd44adb08c723942515ecf512e7c64161c4ff96c8b5c',
               description='Benchmark set for GENESIS 2.0 beta / 1.6 on FUGAKU')
    input_file('tests-2.1.5',
               url='https://github.com/genesis-release-r-ccs/genesis/archive/refs/tags/v2.1.5.tar.gz',
               sha256='622e6dc0bf9db54b2d18165f098044146abbf20837cb6209af2015856469afbf',
               description='Regression tests are prepared for ATDYN, SPDYN, prst_setup (parallel I/O), and analysis tools to check if these programs work correctly.')

    workload('DHFR', executables=['chdir', 'genesis'], input='benchmark-input')
    workload('ApoA1', executables=['chdir', 'genesis'], input='benchmark-input')
    workload('UUN', executables=['chdir', 'genesis'], input='benchmark-input')
    workload('cryoEM', executables=['chdir', 'genesis'], input='tests-2.1.5')

    workload_variable('input', default='{benchmark-input}',
                      description='input/ : benchmark-input root directory',
                      workloads=['DHFR','ApoA1','UUN'])
    workload_variable('input', default='{benchmark-input}/npt/genesis2.0beta/jac_amber/p{n_ranks}.inp',
                      description='jac_amber/ : DHFR (27,346 atoms), AMBER format, soluble system',
                      workloads=['DHFR'])
    workload_variable('input', default='{benchmark-input}/npt/genesis2.0beta/apoa1/p{n_ranks}.inp',
                      description='apoa1/ : apoa1 (92,224 atoms), CHARMM format, soluble system',
                      workloads=['ApoA1'])
    workload_variable('input', default='{benchmark-input}/npt/genesis2.0beta/uun/p{n_ranks}.inp',
                      description='uun/ : uun (216,726 atoms), CHARMM format, membrane+solvent system',
                      workloads=['UUN'])
    workload_variable('input', default='{tests-2.1.5}/tests/regression_test/test_spdyn/cryoEM/All_atom/inp',
                      description='cryoEM/All_atom/ : cryoEM (? atoms), CHARMM format',
                      workloads=['cryoEM'])

    figure_of_merit('Figure of Merit (FOM)', log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'^\s+dynamics\s+=\s+(?P<fom>[-+]?([0-9]*[.])?[0-9]+([eED][-+]?[0-9]+)?)', group_name='fom', units='')

    success_criteria('pass', mode='string', match=r'Figure of Merit \(FOM\)', file='{experiment_run_dir}/{experiment_name}.out')
