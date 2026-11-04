# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.appkit import *


class RcclTests(ExecutableApplication):
    """Performance and correctness tests for RCCL collective operations.

    rccl-tests is AMD's port of nccl-tests and prints the same output, so this
    definition is adapted from Ramble's nccl-tests application.

    https://github.com/ROCm/rccl-tests
    """

    name = "rccl-tests"

    tags('synthetic','ats-6',
         'single-node','multi-node',
         'rccl','mpi','rocm','hip',
         'network-collectives','network-point-to-point',
         'network-bandwidth-bound','network-latency-bound',
         'c++')

    # workload name -> installed executable (src/<test>.cu builds <test>_perf)
    tests = {
        'all-gather': 'all_gather_perf',
        'all-reduce': 'all_reduce_perf',
        'all-reduce-bias': 'all_reduce_bias_perf',
        'all-to-all': 'alltoall_perf',
        'all-to-allv': 'alltoallv_perf',
        'broadcast': 'broadcast_perf',
        'gather': 'gather_perf',
        'hypercube': 'hypercube_perf',
        'reduce': 'reduce_perf',
        'reduce-scatter': 'reduce_scatter_perf',
        'scatter': 'scatter_perf',
        'send-recv': 'sendrecv_perf',
    }
    all_workloads = list(tests.keys())

    for workload_name, binary in tests.items():
        executable(f'{workload_name}-execute',
                   template=[f'{binary} {{additional_args}}'],
                   use_mpi=True)
        workload(workload_name, executables=[f'{workload_name}-execute'])

    workload_variable('num_gpus_per_task', default='1',
                      description='GPUs per MPI rank (-g)',
                      workloads=all_workloads)
    workload_variable('begin_message_size', default='8',
                      description='Smallest message size (-b)',
                      workloads=all_workloads)
    workload_variable('end_message_size', default='8G',
                      description='Largest message size (-e)',
                      workloads=all_workloads)
    workload_variable('message_size_factor', default='2',
                      description='Multiplication factor between sizes (-f)',
                      workloads=all_workloads)
    workload_variable('warmup_iters', default='5',
                      description='Warmup iterations per size (-w)',
                      workloads=all_workloads)
    workload_variable('num_iters', default='100',
                      description='Timed iterations per size (-n)',
                      workloads=all_workloads)
    workload_variable('result_check', default='1',
                      description='1 to check results for correctness, 0 to skip (-c)',
                      workloads=all_workloads)
    workload_variable('additional_args',
                      default='-b {begin_message_size} -e {end_message_size} '
                              '-f {message_size_factor} -g {num_gpus_per_task} '
                              '-w {warmup_iters} -n {num_iters} -c {result_check}',
                      description='Arguments passed to every test',
                      workloads=all_workloads)
    workload_variable('nccl_tests_split_mask', default='',
                      description='How to split communicators, e.g. "0x7" for rail-aligned, "0x0" for world-level',
                      workloads=all_workloads,
                      environment_variable_name='NCCL_TESTS_SPLIT_MASK',
                      expandable=False)

    # One row per message size: size, count, type, redop, root, then
    # time/algbw/busbw/#wrong for out-of-place and in-place
    # (output_name, units, group_name, regex)
    regex_parts = [
        ('Size', 'B', 'size', '[0-9]+'),
        ('Count', 'elements', 'count', '[0-9]+'),
        ('Type', '', 'type', r'\S+'),
        ('Reduction Operator', '', 'redop', r'\S+'),
        ('Root', '', 'root', r'\S+'),
        ('Out of Place Time', 'us', 'ooptime', r'[0-9]+\.?[0-9]+'),
        ('Out of Place Alg Bandwidth', 'GB/s', 'oopalgbw', r'[0-9]+\.?[0-9]+'),
        ('Out of Place Bus Bandwidth', 'GB/s', 'oopbusbw', r'[0-9]+\.?[0-9]+'),
        ('Out of Place Number Wrong', '', 'oopnumwrong', r'\S+'),
        ('In Place Time', 'us', 'iptime', r'[0-9]+\.?[0-9]+'),
        ('In Place Alg Bandwidth', 'GB/s', 'ipalgbw', r'[0-9]+\.?[0-9]+'),
        ('In Place Bus Bandwidth', 'GB/s', 'ipbusbw', r'[0-9]+\.?[0-9]+'),
        ('In Place Number Wrong', '', 'ipnumwrong', r'\S+'),
    ]

    fom_regex = ''
    for regex_part in regex_parts:
        fom_regex += rf'\s+(?P<{regex_part[2]}>{regex_part[3]})'

    figure_of_merit_context('size', output_format='{size}', regex=fom_regex)
    for regex_part in regex_parts:
        figure_of_merit(regex_part[0],
                        fom_regex=fom_regex,
                        units=regex_part[1],
                        group_name=regex_part[2],
                        contexts=['size'])

    # Printed with %g, so the value may be a single digit or use an exponent
    figure_of_merit('Avg. Bus Bandwidth',
                    fom_regex=r'.*Avg bus bandwidth\s+:\s+(?P<bw>[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)',
                    group_name='bw',
                    units='GB/s')
    figure_of_merit('Out of bounds values',
                    fom_regex=r'.*Out of bounds values\s*:\s+(?P<count>[0-9]+)',
                    group_name='count',
                    units='')

    success_criteria('no-wrong-values', mode='string',
                     match=r'Out of bounds values\s*:\s*0\s+OK',
                     file='{log_file}')
