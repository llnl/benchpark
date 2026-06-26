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
            'mpi','c++','llnl-nightly','llnl-monthly','llnl-pr','llnl-weekly']

    executable('setup_experiment',
           template=[
               'cp {branson}/inputs/* {experiment_run_dir}/.',
               'sed -i "s|<photons>[0-9]*</photons>|<photons>{num_particles}</photons>|g" {experiment_run_dir}/{input_file}',
               'grep -q "<photons>" {experiment_run_dir}/{input_file} || sed -i "/<\/common>/ i \  <photons>{num_particles}<\/photons>" {experiment_run_dir}/{input_file}',
               'sed -i "s|<use_gpu_transporter>.*</use_gpu_transporter>|<use_gpu_transporter>{use_gpu}</use_gpu_transporter>|g" {experiment_run_dir}/{input_file}',
               'grep -q "<use_gpu_transporter>" {experiment_run_dir}/{input_file} || sed -i "/<\/common>/ i \  <use_gpu_transporter>{use_gpu}<\/use_gpu_transporter>" {experiment_run_dir}/{input_file}',
               'sed -i "s|<dd_transport_type>.*</dd_transport_type>|<dd_transport_type>{decomposition}</dd_transport_type>|g" {experiment_run_dir}/{input_file}',
               'grep -q "<dd_transport_type>" {experiment_run_dir}/{input_file} || sed -i "/<\/common>/ i \  <dd_transport_type>{decomposition}<\/dd_transport_type>" {experiment_run_dir}/{input_file}',
               'sed -i "s|<particle_storage>.*</particle_storage>|<particle_storage>{layout}</particle_storage>|g" {experiment_run_dir}/{input_file}',
               'grep -q "<particle_storage>" {experiment_run_dir}/{input_file} || sed -i "/<\/common>/ i \  <particle_storage>{layout}<\/particle_storage>" {experiment_run_dir}/{input_file}',
               'sed -i "s|<particle_algorithm>.*</particle_algorithm>|<particle_algorithm>{algorithm}</particle_algorithm>|g" {experiment_run_dir}/{input_file}',
               'grep -q "<particle_algorithm>" {experiment_run_dir}/{input_file} || sed -i "/<\/common>/ i \  <particle_algorithm>{algorithm}<\/particle_algorithm>" {experiment_run_dir}/{input_file}',
               'sed -i "s|<umpire_device_pool_size>.*</umpire_device_pool_size>|<umpire_device_pool_size>{pool}</umpire_device_pool_size>|g" {experiment_run_dir}/{input_file}',
               'grep -q "<umpire_device_pool_size>" {experiment_run_dir}/{input_file} || sed -i "/<\/common>/ i \  <umpire_device_pool_size>{pool}<\/umpire_device_pool_size>" {experiment_run_dir}/{input_file}',
           ])

    executable('p', '{branson}/bin/BRANSON {experiment_run_dir}/{input_file}', use_mpi=True)

    workload('branson', executables=['setup_experiment','p'])
    
    workload_variable('input_file', default='3D_hohlraum_multi_node.xml',
    	description='input file name',
      	workloads=['branson'])

    workload_variable('num_particles', default='250000000',
    	description='procs on node',
      	workloads=['branson'])

    workload_variable('use_gpu', default='FALSE',
    	description='Use GPU (TRUE|FALSE)',
      	workloads=['branson'])

    workload_variable('decomposition', default='PARTICLE_PASS',
    	description='dommain decomposition type (PARTICLE_PASS|REPLICATED)',
      	workloads=['branson'])

    workload_variable('layout', default='SOA',
    	description='storage layout (SOA|AOS)',
      	workloads=['branson'])

    workload_variable('algorithm', default='EVENT',
    	description='particle transport algorithm (EVENT|HISTORY)',
      	workloads=['branson'])

    workload_variable('pool', default='4',
        description='Device pool size in GB',
        workloads=['branson'])

    figure_of_merit('Photons per Second',
                    log_file='{experiment_run_dir}/{experiment_name}.out',
                    fom_regex=r'Photons Per Second \(FOM\):\s+(?P<fom>[0-9]+\.[0-9]*([0-9]*)?e\+[0-9]*)',
                    group_name='fom', units='photons')

    success_criteria('pass', mode='string', match=r'.*', file='{experiment_run_dir}/{experiment_name}.out')
