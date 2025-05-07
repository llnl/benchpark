# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *
from ramble.base_app.benchpark.benchpark import Benchpark as BenchparkApplication


class Laghos(BenchparkApplication):
    """Laghos benchmark"""
    name = "laghos"

    tags = ['asc','engineering','hypre','solver','mfem','cfd','large-scale',
            'multi-node','single-node','mpi','c++','high-order','hydrodynamics',
            'explicit-timestepping','finite-element','time-dependent','ode',
            'full-assembly','partial-assembly',
            'lagrangian','spatial-discretization','unstructured-grid',
            'network-latency-bound','network-collectives','unstructured-grid']

    executable('prob', 'laghos -p {problem} -m {mesh} -rs {rs} -rp {rp} -ms {ms} -d {device}', use_mpi=True)

    workload('triplept', executables=['prob'])

    workload_variable('mesh', default='{laghos}/data/box01_hex.mesh',
                      description='mesh file',
                      workloads=['triplept'])
    workload_variable('mesh_size', default='96',
                      description='number of zones in the mesh described by the mesh file',
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
                      description='cpu or cuda',
                      workloads=['triplept'])
    workload_variable('n_resources', default='1',
                      description='How many processes (CPU cores or GPUs) are required. Should it be a range?',
                      workloads=['triplept'])
    
    workload_variable('process_problem_size', default='{mesh_size}*{rs+1}*{rp+1}/{n_resources}',
                      description='Problem size per process',
                      workloads=['triplept']) 
    workload_variable('total_problem_size', default='{mesh_size}*{rs+1}*{rp+1}',
                      description='Total problem size',
                      workloads=['triplept']) 

    figure_of_merit('Major kernels total time',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'Major kernels total time \(seconds\):\s+(?P<fom>[0-9]+\.[0-9]*(e^[0-9]*)?)',
                    group_name='fom', units='seconds')

    success_criteria('pass', mode='string', match=r'Major kernels total time', file='{experiment_run_dir}/{experiment_name}.out')
