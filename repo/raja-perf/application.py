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

    common = 'raja-perf.exe --checkrun 1 --ltimes_num_m 25 --ltimes_num_d 96 -k Apps_LTIMES -v RAJA_HIP -t kernel_256 -atsc ${CALI_CONFIG_MODE} -atcc ${OTHER_CALI_CONFIG}'
    nresources = 1
    zones=64
    executable('r1', common + f' --ltimes_num_g 220 --size {(220*96*zones)/nresources} -od 1/', use_mpi=True)
    executable('r2', common + f' --ltimes_num_g 220 --size {((220*96*zones)*2**3)/nresources} -od 2/', use_mpi=True)
    executable('r3', common + f' --ltimes_num_g 220 --size {((220*96*zones)*3**3)/nresources} -od 3/', use_mpi=True)
    executable('r4', common + f' --ltimes_num_g 220 --size {((220*96*zones)*4**3)/nresources} -od 4/', use_mpi=True)
    executable('r5', common + f' --ltimes_num_g 220 --size {((220*96*zones)*5**3)/nresources} -od 5/', use_mpi=True)
    executable('r6', common + f' --ltimes_num_g 220 --size {((220*96*zones)*6**3)/nresources} -od 6/', use_mpi=True)
    executable('r7', common + f' --ltimes_num_g 220 --size {((220*96*zones)*7**3)/nresources} -od 7/', use_mpi=True)
    executable('r8', common + f' --ltimes_num_g 220 --size {((220*96*zones)*8**3)/nresources} -od 8/', use_mpi=True)
    executable('r9', common + f' --ltimes_num_g 220 --size {((220*96*zones)*9**3)/nresources} -od 9/', use_mpi=True)
    executable('r10', common + f' --ltimes_num_g 220 --size {((220*96*zones)*10**3)/nresources} -od 10/', use_mpi=True)
    executable('r11', common + f' --ltimes_num_g 220 --size {((220*96*zones)*11*3)/nresources} -od 11/', use_mpi=True)

    executable('r12', common + f' --ltimes_num_g 320 --size {(320*96*zones)/nresources} -od 12/', use_mpi=True)
    executable('r13', common + f' --ltimes_num_g 320 --size {((320*96*zones)*2**3)/nresources} -od 13/', use_mpi=True)
    executable('r14', common + f' --ltimes_num_g 320 --size {((320*96*zones)*3**3)/nresources} -od 14/', use_mpi=True)
    executable('r15', common + f' --ltimes_num_g 320 --size {((320*96*zones)*4**3)/nresources} -od 15/', use_mpi=True)
    executable('r16', common + f' --ltimes_num_g 320 --size {((320*96*zones)*5**3)/nresources} -od 16/', use_mpi=True)
    executable('r17', common + f' --ltimes_num_g 320 --size {((320*96*zones)*6**3)/nresources} -od 17/', use_mpi=True)
    executable('r18', common + f' --ltimes_num_g 320 --size {((320*96*zones)*7**3)/nresources} -od 18/', use_mpi=True)
    executable('r19', common + f' --ltimes_num_g 320 --size {((320*96*zones)*8**3)/nresources} -od 19/', use_mpi=True)
    executable('r20', common + f' --ltimes_num_g 320 --size {((320*96*zones)*9**3)/nresources} -od 20/', use_mpi=True)
    executable('r21', common + f' --ltimes_num_g 320 --size {((320*96*zones)*10**3)/nresources} -od 21/', use_mpi=True)
    executable('r22', common + f' --ltimes_num_g 320 --size {((320*96*zones)*11**3)/nresources} -od 22/', use_mpi=True)

    executable('r23', common + f' --ltimes_num_g 360 --size {(360*96*zones)/nresources} -od 23/', use_mpi=True)
    executable('r24', common + f' --ltimes_num_g 360 --size {((360*96*zones)*2**3)/nresources} -od 24/', use_mpi=True)
    executable('r25', common + f' --ltimes_num_g 360 --size {((360*96*zones)*3**3)/nresources} -od 25/', use_mpi=True)
    executable('r26', common + f' --ltimes_num_g 360 --size {((360*96*zones)*4**3)/nresources} -od 26/', use_mpi=True)
    executable('r27', common + f' --ltimes_num_g 360 --size {((360*96*zones)*5**3)/nresources} -od 27/', use_mpi=True)
    executable('r28', common + f' --ltimes_num_g 360 --size {((360*96*zones)*6**3)/nresources} -od 28/', use_mpi=True)
    executable('r29', common + f' --ltimes_num_g 360 --size {((360*96*zones)*7**3)/nresources} -od 29/', use_mpi=True)
    executable('r30', common + f' --ltimes_num_g 360 --size {((360*96*zones)*8**3)/nresources} -od 30/', use_mpi=True)
    executable('r31', common + f' --ltimes_num_g 360 --size {((360*96*zones)*9**3)/nresources} -od 31/', use_mpi=True)
    executable('r32', common + f' --ltimes_num_g 360 --size {((360*96*zones)*10**3)/nresources} -od 32/', use_mpi=True)
    executable('r33', common + f' --ltimes_num_g 360 --size {((360*96*zones)*11**3)/nresources} -od 33/', use_mpi=True)

    # common = 'raja-perf.exe --checkrun 1 --ltimes_num_m 25 --ltimes_num_d 96 -k Apps_LTIMES -v RAJA_Seq -t kernel -atsc ${CALI_CONFIG_MODE} -atcc ${OTHER_CALI_CONFIG}'
    # nresources = 112
    # zones=112
    # executable('r1', common + f' --ltimes_num_g 220 --size {(220*96*zones)/nresources} -od 1/', use_mpi=True)
    # executable('r2', common + f' --ltimes_num_g 220 --size {((220*96*zones)*2**3)/nresources} -od 2/', use_mpi=True)
    # executable('r3', common + f' --ltimes_num_g 220 --size {((220*96*zones)*3**3)/nresources} -od 3/', use_mpi=True)
    # executable('r4', common + f' --ltimes_num_g 220 --size {((220*96*zones)*4**3)/nresources} -od 4/', use_mpi=True)
    # executable('r5', common + f' --ltimes_num_g 220 --size {((220*96*zones)*5**3)/nresources} -od 5/', use_mpi=True)
    # executable('r6', common + f' --ltimes_num_g 220 --size {((220*96*zones)*6**3)/nresources} -od 6/', use_mpi=True)
    # executable('r7', common + f' --ltimes_num_g 220 --size {((220*96*zones)*7**3)/nresources} -od 7/', use_mpi=True)
    # executable('r8', common + f' --ltimes_num_g 220 --size {((220*96*zones)*8**3)/nresources} -od 8/', use_mpi=True)
    # executable('r9', common + f' --ltimes_num_g 220 --size {((220*96*zones)*9**3)/nresources} -od 9/', use_mpi=True)
    # executable('r10', common + f' --ltimes_num_g 220 --size {((220*96*zones)*10**3)/nresources} -od 10/', use_mpi=True)
    # executable('r11', common + f' --ltimes_num_g 220 --size {((220*96*zones)*11*3)/nresources} -od 11/', use_mpi=True)

    # executable('r12', common + f' --ltimes_num_g 320 --size {(320*96*zones)/nresources} -od 12/', use_mpi=True)
    # executable('r13', common + f' --ltimes_num_g 320 --size {((320*96*zones)*2**3)/nresources} -od 13/', use_mpi=True)
    # executable('r14', common + f' --ltimes_num_g 320 --size {((320*96*zones)*3**3)/nresources} -od 14/', use_mpi=True)
    # executable('r15', common + f' --ltimes_num_g 320 --size {((320*96*zones)*4**3)/nresources} -od 15/', use_mpi=True)
    # executable('r16', common + f' --ltimes_num_g 320 --size {((320*96*zones)*5**3)/nresources} -od 16/', use_mpi=True)
    # executable('r17', common + f' --ltimes_num_g 320 --size {((320*96*zones)*6**3)/nresources} -od 17/', use_mpi=True)
    # executable('r18', common + f' --ltimes_num_g 320 --size {((320*96*zones)*7**3)/nresources} -od 18/', use_mpi=True)
    # executable('r19', common + f' --ltimes_num_g 320 --size {((320*96*zones)*8**3)/nresources} -od 19/', use_mpi=True)
    # executable('r20', common + f' --ltimes_num_g 320 --size {((320*96*zones)*9**3)/nresources} -od 20/', use_mpi=True)
    # executable('r21', common + f' --ltimes_num_g 320 --size {((320*96*zones)*10**3)/nresources} -od 21/', use_mpi=True)
    # executable('r22', common + f' --ltimes_num_g 320 --size {((320*96*zones)*11**3)/nresources} -od 22/', use_mpi=True)

    # executable('r23', common + f' --ltimes_num_g 360 --size {(360*96*zones)/nresources} -od 23/', use_mpi=True)
    # executable('r24', common + f' --ltimes_num_g 360 --size {((360*96*zones)*2**3)/nresources} -od 24/', use_mpi=True)
    # executable('r25', common + f' --ltimes_num_g 360 --size {((360*96*zones)*3**3)/nresources} -od 25/', use_mpi=True)
    # executable('r26', common + f' --ltimes_num_g 360 --size {((360*96*zones)*4**3)/nresources} -od 26/', use_mpi=True)
    # executable('r27', common + f' --ltimes_num_g 360 --size {((360*96*zones)*5**3)/nresources} -od 27/', use_mpi=True)
    # executable('r28', common + f' --ltimes_num_g 360 --size {((360*96*zones)*6**3)/nresources} -od 28/', use_mpi=True)
    # executable('r29', common + f' --ltimes_num_g 360 --size {((360*96*zones)*7**3)/nresources} -od 29/', use_mpi=True)
    # executable('r30', common + f' --ltimes_num_g 360 --size {((360*96*zones)*8**3)/nresources} -od 30/', use_mpi=True)
    # executable('r31', common + f' --ltimes_num_g 360 --size {((360*96*zones)*9**3)/nresources} -od 31/', use_mpi=True)
    # executable('r32', common + f' --ltimes_num_g 360 --size {((360*96*zones)*10**3)/nresources} -od 32/', use_mpi=True)
    # executable('r33', common + f' --ltimes_num_g 360 --size {((360*96*zones)*11**3)/nresources} -od 33/', use_mpi=True)


    workload('suite', executables=[f'r{i}' for i in range(1, 34)])

    figure_of_merit('All tests pass', log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'(?P<tpass>DONE)!!!...', group_name='tpass', units='')

    success_criteria('pass', mode='string', match=r'DONE!!!....', file='{experiment_run_dir}/{experiment_name}.out')
