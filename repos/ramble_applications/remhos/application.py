# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Remhos(ExecutableApplication):
    """Remhos benchmark"""
    name = "remhos"

    tags = ['asc','engineering','mfem','cfd','large-scale',
            'multi-node','single-node','mpi','c++','high-order','hydrodynamics',
            'explicit-timestepping','finite-element','time-dependent','ode',
            'full-assembly','partial-assembly',
            'lagrangian','spatial-discretization','unstructured-grid',
            'network-latency-bound','network-collectives','unstructured-grid',
            'llnl-nightly','llnl-monthly','llnl-pr','llnl-weekly']

    executable('2d', 'remhos' +
                     ' -dim 2 ' +
                     ' -epm {epm}' +
                     ' -o {o}' +
                     ' -p {p}' +
                     ' -dt {dt} -tf {tf}' +
                     ' -ho {ho} -lo {lo}' +
                     ' -fct {fct}' +
                     ' -vs {vs}' +
                     ' -ms {ms}' +
                     ' -no-vis' +
                     ' --dev-pool-size {pool}' +
                     ' -pa' +
                     ' -d {device}' +
                     ' {gam}',
                     use_mpi=True)

    executable('3d', 'remhos' +
                     ' -dim 3' +
                     ' -epm {epm}' +
                     ' -o {o}' +
                     ' -p {p}' +
                     ' -dt {dt} -tf {tf}' +
                     ' -ho {ho} -lo {lo}' +
                     ' -fct {fct}' +
                     ' -vs {vs}' +
                     ' -ms {ms}' +
                     ' -no-vis' +
                     ' --dev-pool-size {pool}' +
                     ' -pa' +
                     ' -d {device}' +
                     ' {gam}',
                     use_mpi=True)

    workload('2d', executables=['2d'])
    workload('3d', executables=['3d'])
    
    #workload_variable('mesh', default='{remhos}/data/periodic-square.mesh',
    #   description='mesh file',
    #  workloads=[''])

    workload_variable('epm', default='1024',
        description='elements per mpi task',
        workloads=['2d','3d'])

    workload_variable('o', default='2',
        description='order (degree) of the finite element solution',
        workloads=['2d','3d'])

    workload_variable('p', default='5',
        description='problem number',
        workloads=['remhos'])
    
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

    workload_variable('pool', default='4',
        description='Device pool size',
        workloads=['2d', '3d'])

    workload_variable('device', default='cpu',
        description='cpu, cuda, hip or raja-gpu',
        workloads=['2d','3d'])

    workload_variable('gam', default='--no-gpu-aware-mpi',
        description='--gpu-aware-mpi or --no-gpu-aware-mpi',
        workloads=['2d','3d'])

    figure_of_merit("FOM", log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'FOM:\s+(?P<fom>[0-9]*\.[0-9]*)', group_name='fom', units='megadofs x time steps / second')
    #FOM_regex=r'(?<=Merit)\s+[\+\-]*[0-9]*\.*[0-9]+e*[\+\-]*[0-9]*'
    success_criteria('valid', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')

