# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class SalmonTddft(SpackApplication):
    """Salmon-tddft benchmark"""
    name = "salmon-tddft"

    tags = ['mpi','openmp']

    executable('pre-process', 'cp {input_path}/* .', use_mpi=False)

    executable('post-process', 'cp -r ./data_for_restart {input_path}', use_mpi=False)

    executable('link-restart', 'ln -s -T {restart_data} restart', use_mpi=False)
               
    executable('execute', '-stdin {input_data} ' +
               'salmon' , use_mpi=True)

    input_file('salmon-v2_gs', url='http://salmon-tddft.jp/download/SALMON-v.2.2.0.tar.gz',
               md5='d71436df3a1ad507f665abb8453eee15',
               description='')
    input_file('salmon-v2_rt', url='http://salmon-tddft.jp/download/SALMON-v.2.2.0.tar.gz',
               md5='d71436df3a1ad507f665abb8453eee15',
               description='')
               
    workload('gs', executables=['pre-process', 'execute'], input='salmon-v2_gs')
    workload('rt', executables=['pre-process', 'link-restart', 'execute'], input='salmon-v2_rt')
    
   # workload_variable('input_path', default='{salmon-v2}/samples/{exercise}',
   #                   description='Input path for sample exercise',
   #                   workloads=['gs','rt'])
   # workload_variable('input_data', default='{salmon-v2}/samples/{exercise}/{inp_file}',
   #                   description='Input data for sample exercise',
   #                   workloads=['gs','rt'])
    workload_variable('input_path', default='{salmon-v2_gs}/samples/exercise_01_C2H2_gs',
                      description='Input path for C2H2_gs',
                      workload='gs')
    workload_variable('input_data', default='{salmon-v2_gs}/samples/exercise_01_C2H2_gs/C2H2_gs.inp',
                      description='Input data for C2H2_gs',
                      workload='gs')
    workload_variable('input_path', default='{salmon-v2_rt}/samples/exercise_03_C2H2_rt',
                      description='Input path for C2H2_rt',
                      workload='rt')
    workload_variable('input_data', default='{salmon-v2_rt}/samples/exercise_03_C2H2_rt/C2H2_rt_pulse.inp',
                      description='Input data for C2H2_rt',
                      workload='rt')
   # workload_variable('restart_data', default='{salmon-v2_rt}/samples/exercise_01_C2H2_gs/data_for_restart',
   #                   description='Restart data for C2H2_rt',
   #                   workload='rt')

#    figure_of_merit('Figure of Merit (FOM)', log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'Figure of Merit \(FOM\):\s+(?P<fom>[0-9]+\.[0-9]*(e^[0-9]*)?)', group_name='fom', units='')

    #TODO: Fix the FOM success_criteria(...)
#    success_criteria('pass', mode='string', match=r'Figure of Merit \(FOM\)', file='{experiment_run_dir}/{experiment_name}.out')

