# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class RajaPerf(ExecutableApplication):
    """RAJA Performance suite"""
    name = "raja-perf"

    tags = ['asc','single-node','sub-node','structured-grid',
            'atomics','simd','vectorization','register-pressure',
            'high-memory-bandwidth','regular-memory-access',
            'mpi','network-point-to-point','network-latency-bound',
            'c++','raja','sycl','builtin-caliper']

    register_phase(
        "compute_cali_args", pipeline="setup", run_before=["make_experiments"]
    )

    def _compute_cali_args(self, workspace, app_inst=None):
        cali_args = ""
        if "caliper_metadata" in app_inst.variables:
            cali_args = "-atsc ${CALI_CONFIG_MODE} -atcc ${OTHER_CALI_CONFIG}"
        app_inst.variables["custom_cali_args"] = cali_args

    executable('run', 'raja-perf.exe --size {process_problem_size} {custom_cali_args}', use_mpi=True)

    workload('suite', executables=['run'])

    figure_of_merit('All tests pass', log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'(?P<tpass>DONE)!!!...', group_name='tpass', units='')

    success_criteria('pass', mode='string', match=r'DONE!!!....', file='{experiment_run_dir}/{experiment_name}.out')
