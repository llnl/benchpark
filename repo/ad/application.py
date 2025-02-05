# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Ad(ExecutableApplication):
    """AD benchmark"""
    name = "ad"

    tags = ['mpi','c','c++','automatic-differentiation','compiler-transformation']

    executable('c_interface_test', 'c_interface_test', use_mpi=True)

    workload('ad', executables=['c_interface_test'])
    
    #figure_of_merit('Photons per Second',
    #                log_file='{experiment_run_dir}/{experiment_name}.out',
    #                fom_regex=r'Photons Per Second \(FOM\):\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)?e\+[0-9]*)',
    #                group_name='fom', units='photons')

    #success_criteria('pass', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')
