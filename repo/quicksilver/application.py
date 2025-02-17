# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Quicksilver(ExecutableApplication):
    """Quicksilver benchmark"""
    name = "quicksilver"

    tags = ['asc','montecarlo',
            'single-node',
            'high-branching',
            'irregular-memory-access',
            'mpi',
            'c++','openmp']

    executable('run', 'qs'+
            ' -i {i}' +
            ' -X {X}' +
            ' -Y {Y}' +
            ' -Z {Z}' +
            ' -I {I}' +
            ' -J {J}' +
            ' -K {K}' +
            ' -x {x}' +
            ' -y {y}' +
            ' -z {z}' +
            ' -n {n}'
            , use_mpi=True)

    workload('quicksilver', executables=['run'])
    #not sure if these variables are necessary
    workload_variable('D', default='',
                      description='time step (seconds)',
                      workloads=['quicksilver'])
    workload_variable('f', default='',
                      description='max random mesh node displacement',
                      workloads=['quicksilver'])
    workload_variable('i', default='{quicksilver}/Examples/CTS2_Benchmark/CTS2.inp',
                      description='name of input file',
                      workloads=['quicksilver'])
    workload_variable('e', default='',
                      description='',
                      workloads=['quicksilver'])
    workload_variable('S', default='',
                      description='name of cross section output file',
                      workloads=['quicksilver'])
    workload_variable('l', default='',
                      description='enable/disable load balancing',
                      workloads=['quicksilver'])
    
    workload_variable('c', default='',
                      description='enable/disable cycle timers',
                      workloads=['quicksilver'])

    workload_variable('t', default='',
                      description='set thread debug level to 1, 2, 3',
                      workloads=['quicksilver'])

    workload_variable('X', default='',
                      description='x-size of simulation (cm)',
                      workloads=['quicksilver'])

    workload_variable('Y', default='',
                      description='y-size of simulation (cm)',
                      workloads=['quicksilver'])

    workload_variable('Z', default='',
                      description='z-size of simulation (cm)',
                      workloads=['quicksilver'])

    workload_variable('n', default='',
                      description='number of particles',
                      workloads=['quicksilver'])

    workload_variable('g', default='',
                      description='number of particles in a vault/batch',
                      workloads=['quicksilver'])


    workload_variable('b', default='',
                      description='number of vault/batch to start (sets batchSize automatically)',
                      workloads=['quicksilver'])

    workload_variable('N', default='',
                      description='number of time steps',
                      workloads=['quicksilver'])

    workload_variable('x', default='',
                      description='number of mesh elements in x',
                      workloads=['quicksilver'])

    workload_variable('y', default='',
                      description='number of mesh elements in y',
                      workloads=['quicksilver'])

    workload_variable('z', default='',
                      description='number of mesh elements in z',
                      workloads=['quicksilver'])

    workload_variable('s', default='',
                      description='random number seed',
                      workloads=['quicksilver'])

    workload_variable('I', default='',
                      description='number of MPI ranks in x',
                      workloads=['quicksilver'])

    workload_variable('J', default='',
                      description='number of MPI ranks in y',
                      workloads=['quicksilver'])

    workload_variable('K', default='',
                      description='number of MPI ranks in z',
                      workloads=['quicksilver'])

    workload_variable('B', default='',
                      description='number of balance tally replications',
                      workloads=['quicksilver'])

    workload_variable('F', default='',
                      description='number of scalar flux tally replications',
                      workloads=['quicksilver'])

    workload_variable('C', default='',
                      description='number of scalar cell tally replications',
                      workloads=['quicksilver'])


    #FOM_regex=r'(?<=Merit)\s+[\+\-]*[0-9]*\.*[0-9]+e*[\+\-]*[0-9]*'
    figure_of_merit("FOM", log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'Figure Of Merit\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)+e\+?[0-9]*)', group_name='fom', units='Num Segments / Cycle Tracking Time')

    figure_of_merit("avg cycleTracking", log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'cycleTracking +[0-9]+\s+[0-9]+\.[0-9]*[0-9]*e\+?[0-9]+\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)+e\+?[0-9]*)', group_name='fom', units='Cumulative microseconds avg')
    success_criteria('valid', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')

