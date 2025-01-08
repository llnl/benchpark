# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Remhos(ExecutableApplication):
    """Remhos benchmark"""
    name = "remhos"
#TODO: add -ms flag once it's implemented
    executable('2d', 'remhos'+' -dim 2 -epm 1024'+' -p 14'+' -rs {rs2d}'+' -o 3 -dt {dt}'+' -tf {tf}'+' -ho {ho}' ' -lo {lo}'+' -fct {fct}'+' -vs {vs}'+' -ms {ms}'+' -d {device}'+' -pa -no-vis', use_mpi=True)
    executable('3d', 'remhos'+' -dim 3 -epm 512'+' -p 10'+' -rs {rs3d}'+' -o 2'+' -dt {dt}'+' -tf {tf}'+' -ho {ho}' ' -lo {lo}'+' -fct {fct}'+' -vs {vs}'+' -ms {ms}'+' -d {device}'+' -pa -no-vis', use_mpi=True)
    workload('2d', executables=['2d'])
    workload('3d', executables=['3d'])
    
    #workload_variable('mesh', default='{remhos}/data/periodic-square.mesh',
     #   description='mesh file',
      #  workloads=[''])

    #workload_variable('p', default='5',
     #   description='problem number',
     #   workloads=['remhos'])
    
    workload_variable('rs2d', default='4',
        description='number of serial refinements',
        workloads=['2d'])
    
    workload_variable('rs3d', default='3',
        description='number of serial refinements',
        workloads=['3d'])

    #workload_variable('rp', default='',
     #   description='number of parallel refinements',
      #  workloads=['remhos'])

    workload_variable('o', default='2',
        description='',
        workloads=['2d','3d'])

    workload_variable('dt', default='-1.0',
        description='time step',
        workloads=['2d','3d'])

    workload_variable('tf', default='0.5',
        description='time final',
        workloads=['2d','3d'])
    
    workload_variable('ho', default='3',
        description='high order solver',
        workloads=['2d','3d'])

    workload_variable('lo', default='5',
        description='low order solver',
        workloads=['2d','3d'])

    workload_variable('fct', default='2',
        description='fct type',
        workloads=['2d','3d'])

    workload_variable('vs', default='1',
        description='vs',
        workloads=['2d','3d'])

    workload_variable('ms', default='5',
        description='ms',
        workloads=['2d','3d'])
    workload_variable('device', default='cpu',
        description='cpu or cuda',
        workloads=['2d','3d'])

    figure_of_merit("FOM", log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'FOM:\s+(?P<fom>[0-9]*\.[0-9]*)', group_name='fom', units='megadofs x time steps / second')
    #FOM_regex=r'(?<=Merit)\s+[\+\-]*[0-9]*\.*[0-9]+e*[\+\-]*[0-9]*'
    success_criteria('valid', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')

