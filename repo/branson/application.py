# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Branson(ExecutableApplication):
    """Branson benchmark"""
    name = "branson"

    tags = ['asc','montecarlo','particles',
            'high-branching','irregular-memory-access',
            'mpi','c++','cuda']

    executable('setup_experiment',
           template=[
               'cp {branson}/inputs/* {experiment_run_dir}/.',
               'sed -i "s|<photons>250000000</photons>|<photons>{num_particles}</photons>|g" {experiment_run_dir}/{input_file}'
           ])

    executable('p', '{branson}/bin/BRANSON {experiment_run_dir}/{input_file}', use_mpi=True)

    workload('branson', executables=['setup_experiment','p'])
    
    workload_variable('input_file', default='3D_hohlraum_multi_node.xml',
    	description='input file name',
      	workloads=['branson'])


    workload_variable('num_particles', default='250000000',
    	description='procs on node',
      	workloads=['branson'])


    figure_of_merit('Photons per Second',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'Photons Per Second \(FOM\):\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)?e\+[0-9]*)',
                    group_name='fom', units='photons')

    success_criteria('pass', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')
