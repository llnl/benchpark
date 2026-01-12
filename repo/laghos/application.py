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

    executable('triplept', 'laghos' +
                       ' -p 3' +
                       ' -m {mesh}' +
                       ' -nx {nx} -ny {ny} -nz {nz}' +
                       ' -rs {rs} -rp {rp}' +
                       ' -ms {ms}' +
                       ' -ok {ok} -ot {ot} -oq {oq}' +
                       ' {nc} --mem --fom {gam}' +
                       ' --dev-pool-size {pool}' +
                       ' -d {device}' +
                       ' {assembly}',
                       use_mpi=True)

    executable('sedov', 'laghos' +
                       ' -p 1' +
                       ' -m {mesh}' +
                       ' -nx {nx} -ny {ny} -nz {nz}' +
                       ' -rs {rs} -rp {rp}' +
                       ' -ms {ms}' +
                       ' -ok {ok} -ot {ot} -oq {oq}' +
                       ' {nc} --mem --fom {gam}' +
                       ' --dev-pool-size {pool}' +
                       ' -d {device}' +
                       ' {assembly}',
                       use_mpi=True)

    workload('triplept', executables=['triplept'])
    workload('sedov', executables=['sedov'])

    workload_variable('mesh', default='default',
            description='mesh file',
            workloads=['*'])

    workload_variable('nx', default='2',
            description='Elements in x-dimension',
            workloads=['*'])
        
    workload_variable('ny', default='2',
            description='Elements in y-dimension',
            workloads=['*'])
        
    workload_variable('nz', default='2',
            description='Elements in z-dimension',
            workloads=['*'])
        
    workload_variable('problem', default='3',
            description='problem number',
            workloads=['*'])
        
    workload_variable('rs', default='2',
            description='number of serial refinements',
            workloads=['*'])
    
    workload_variable('rp', default='0',
            description='number of parallel refinements',
            workloads=['*'])
    
    workload_variable('ms', default='250',
            description='max number of steps',
            workloads=['*'])

    workload_variable('ok', default='1',
            description='Order (degree) of the kinematic finite element space',
            workloads=['*'])

    workload_variable('ot', default='0',
            description='Order (degree) of the thermodynamic finite element space',
            workloads=['*'])

    workload_variable('oq', default='-1',
            description='Order  of the integration rule',
            workloads=['*'])

    workload_variable('pool', default='4',
        description='Device pool size',
        workloads=['*'])

    workload_variable('device', default='cpu',
        description='cpu, cuda or hip',
        workloads=['*'])

    workload_variable('gam', default='--no-gpu-aware-mpi',
        description='--gpu-aware-mpi or --no-gpu-aware-mpi',
        workloads=['*'])

    workload_variable('nc', default='-nc',
        description='Use non-conforming meshes. Requires a 2D or 3D mesh.',
        workloads=['*'])

    workload_variable('assembly', default='-pa',
            description='Activate 1D tensor-based assembly (partial assembly).',
            workloads=['*'])
    
    workload_variable('tf', default='0.8',
            description='Final time; start time is 0.',
            workloads=['*'])
    
    figure_of_merit('Major kernels total time',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'Major kernels total time \(seconds\):\s+(?P<fom>[0-9]+\.[0-9]*(e^[0-9]*)?)',
                    group_name='fom', units='seconds')

    success_criteria('pass', mode='string', match=r'Major kernels total time', file='{experiment_run_dir}/{experiment_name}.out')
