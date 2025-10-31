# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Laghos(ExecutableApplication):
    """Laghos benchmark"""
    name = "laghos"

    tags = ['asc','engineering','hypre','solver','mfem','cfd','large-scale',
            'multi-node','single-node','mpi','c++','high-order','hydrodynamics',
            'explicit-timestepping','finite-element','time-dependent','ode',
            'full-assembly','partial-assembly',
            'lagrangian','spatial-discretization','unstructured-grid',
            'network-latency-bound','network-collectives','unstructured-grid']

    executable('prob', 'laghos -p {problem} -m {mesh} -nx {nx} -ny {ny} -nz {nz} -rs {rs} -rp {rp} -ms {ms} --fom {gam} -d {device} {assembly} -tf {tf}', use_mpi=True)

    workload('triplept', executables=['prob'])

    workload_variable('mesh', default='default',
            description='mesh file',
            workloads=['triplept'])

    workload_variable('nx', default='2',
            description='Elements in x-dimension',
            workloads=['triplept'])
        
    workload_variable('ny', default='2',
            description='Elements in y-dimension',
            workloads=['triplept'])
        
    workload_variable('nz', default='2',
            description='Elements in z-dimension',
            workloads=['triplept'])
        
    workload_variable('problem', default='3',
            description='problem number',
            workloads=['triplept'])
        
    workload_variable('rs', default='2',
            description='number of serial refinements',
            workloads=['triplept'])
    
    workload_variable('rp', default='0',
            description='number of parallel refinements',
            workloads=['triplept'])
    
    workload_variable('ms', default='250',
            description='max number of steps',
            workloads=['triplept'])

    workload_variable('device', default='cpu',
        description='cpu, cuda or hip',
        workloads=['triplept'])

    workload_variable('gam', default='--no-gpu-aware-mpi',
        description='--gpu-aware-mpi or --no-gpu-aware-mpi',
        workloads=['triplept'])

    workload_variable('assembly', default='-pa',
            description='Activate 1D tensor-based assembly (partial assembly).',
            workloads=['triplept'])
    
    workload_variable('tf', default='0.6',
            description='Final time; start time is 0.',
            workloads=['triplept'])
    
    figure_of_merit('Major kernels total time',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'Major kernels total time \(seconds\):\s+(?P<fom>[0-9]+\.[0-9]*(e^[0-9]*)?)',
                    group_name='fom', units='seconds')

    success_criteria('pass', mode='string', match=r'Major kernels total time', file='{experiment_run_dir}/{experiment_name}.out')
