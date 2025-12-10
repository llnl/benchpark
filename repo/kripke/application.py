# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Kripke(ExecutableApplication):
    """Kripke benchmark uses RAJA Portability Layer"""
    name = "Kripke"

    tags = ['asc','transport','deterministic','structured-grid',
            'large-scale','multi-node','single-node','c++','raja',
            'simd','vectorization','register-pressure','high-fp','atomics','high-branching',
            'high-memory-bandwidth','large-memory-footprint','regular-memory-access',
            'mpi','network-latency-bound','network-collectives']

    # executable('kripke', 'kripke.exe' +
    #                  ' --groups {ngroups}' +
    #                  ' --legendre {lorder}' +
    #                  ' --quad {nquad}' +
    #                  ' --zones {nzx},{nzy},{nzz}' +
    #                  #' --sigt {sigt0},{sigt1},{sigt2}' +
    #                  #' --sigs {sigs0},{sigs1},{sigs2}' +
    #                  ' --arch {arch}' +
    #                  ' --layout {layout}' +
    #                  ' --procs {npx},{npy},{npz}' +
    #                  #' --dset {ds}' +
    #                  #' --gset {gs}' +
    #                  #' --zset {nzsetx},{nzsety},{nzsetz}' +
    #                  ' --niter {niter}', use_mpi=True)
    #                  #' --pmethod {method}'

    common = 'kripke.exe --arch {arch} --layout {layout} --procs 1,1,1 --niter 1 --legendre 4 --quad 96 --gset 1 '

    executable('k1',  common + ' --groups 220 --zones 4,4,4',   use_mpi=True)
    executable('k2',  common + ' --groups 220 --zones 8,8,8', use_mpi=True)
    executable('k3',  common + ' --groups 220 --zones 12,12,12', use_mpi=True)
    executable('k4',  common + ' --groups 220 --zones 16,16,16', use_mpi=True)
    executable('k5',  common + ' --groups 220 --zones 20,20,20', use_mpi=True)
    executable('k6',  common + ' --groups 220 --zones 24,24,24', use_mpi=True)
    executable('k7',  common + ' --groups 220 --zones 28,28,28', use_mpi=True)
    executable('k8',  common + ' --groups 220 --zones 32,32,32', use_mpi=True)
    executable('k9',  common + ' --groups 220 --zones 36,36,36', use_mpi=True)
    executable('k10', common + ' --groups 220 --zones 40,40,40', use_mpi=True)
    executable('k11', common + ' --groups 220 --zones 44,44,44', use_mpi=True)

    executable('k12', common + ' --groups 320 --zones 4,4,4',    use_mpi=True)
    executable('k13', common + ' --groups 320 --zones 8,8,8',  use_mpi=True)
    executable('k14', common + ' --groups 320 --zones 12,12,12', use_mpi=True)
    executable('k15', common + ' --groups 320 --zones 16,16,16', use_mpi=True)
    executable('k16', common + ' --groups 320 --zones 20,20,20', use_mpi=True)
    executable('k17', common + ' --groups 320 --zones 24,24,24', use_mpi=True)
    executable('k18', common + ' --groups 320 --zones 28,28,28', use_mpi=True)
    executable('k19', common + ' --groups 320 --zones 32,32,32', use_mpi=True)
    executable('k20', common + ' --groups 320 --zones 36,36,36', use_mpi=True)
    executable('k21', common + ' --groups 320 --zones 40,40,40', use_mpi=True)
    executable('k22', common + ' --groups 320 --zones 44,44,44', use_mpi=True)

    executable('k23', common + ' --groups 360 --zones 4,4,4',    use_mpi=True)
    executable('k24', common + ' --groups 360 --zones 8,8,8',  use_mpi=True)
    executable('k25', common + ' --groups 360 --zones 12,12,12', use_mpi=True)
    executable('k26', common + ' --groups 360 --zones 16,16,16', use_mpi=True)
    executable('k27', common + ' --groups 360 --zones 20,20,20', use_mpi=True)
    executable('k28', common + ' --groups 360 --zones 24,24,24', use_mpi=True)
    executable('k29', common + ' --groups 360 --zones 28,28,28', use_mpi=True)
    executable('k30', common + ' --groups 360 --zones 32,32,32', use_mpi=True)
    executable('k31', common + ' --groups 360 --zones 36,36,36', use_mpi=True)
    executable('k32', common + ' --groups 360 --zones 40,40,40', use_mpi=True)
    executable('k33', common + ' --groups 360 --zones 44,44,44', use_mpi=True)

    # common = 'kripke.exe --arch {arch} --layout {layout} --procs 2,2,1 --niter 1 --legendre 4 --quad 96 --gset 1 '

    # executable('k1',  common + ' --groups 220 --zones 8,8,4',   use_mpi=True)
    # executable('k2',  common + ' --groups 220 --zones 16,16,8', use_mpi=True)
    # executable('k3',  common + ' --groups 220 --zones 24,24,12', use_mpi=True)
    # executable('k4',  common + ' --groups 220 --zones 32,32,16', use_mpi=True)
    # executable('k5',  common + ' --groups 220 --zones 40,40,20', use_mpi=True)
    # executable('k6',  common + ' --groups 220 --zones 48,48,24', use_mpi=True)
    # executable('k7',  common + ' --groups 220 --zones 56,56,28', use_mpi=True)
    # executable('k8',  common + ' --groups 220 --zones 64,64,32', use_mpi=True)
    # executable('k9',  common + ' --groups 220 --zones 72,72,36', use_mpi=True)
    # executable('k10', common + ' --groups 220 --zones 80,80,40', use_mpi=True)
    # executable('k11', common + ' --groups 220 --zones 88,88,44', use_mpi=True)

    # executable('k12', common + ' --groups 320 --zones 8,8,4',    use_mpi=True)
    # executable('k13', common + ' --groups 320 --zones 16,16,8',  use_mpi=True)
    # executable('k14', common + ' --groups 320 --zones 24,24,12', use_mpi=True)
    # executable('k15', common + ' --groups 320 --zones 32,32,16', use_mpi=True)
    # executable('k16', common + ' --groups 320 --zones 40,40,20', use_mpi=True)
    # executable('k17', common + ' --groups 320 --zones 48,48,24', use_mpi=True)
    # executable('k18', common + ' --groups 320 --zones 56,56,28', use_mpi=True)
    # executable('k19', common + ' --groups 320 --zones 64,64,32', use_mpi=True)
    # executable('k20', common + ' --groups 320 --zones 72,72,36', use_mpi=True)
    # executable('k21', common + ' --groups 320 --zones 80,80,40', use_mpi=True)
    # executable('k22', common + ' --groups 320 --zones 88,88,44', use_mpi=True)

    # executable('k23', common + ' --groups 360 --zones 8,8,4',    use_mpi=True)
    # executable('k24', common + ' --groups 360 --zones 16,16,8',  use_mpi=True)
    # executable('k25', common + ' --groups 360 --zones 24,24,12', use_mpi=True)
    # executable('k26', common + ' --groups 360 --zones 32,32,16', use_mpi=True)
    # executable('k27', common + ' --groups 360 --zones 40,40,20', use_mpi=True)
    # executable('k28', common + ' --groups 360 --zones 48,48,24', use_mpi=True)
    # executable('k29', common + ' --groups 360 --zones 56,56,28', use_mpi=True)
    # executable('k30', common + ' --groups 360 --zones 64,64,32', use_mpi=True)
    # executable('k31', common + ' --groups 360 --zones 72,72,36', use_mpi=True)
    # executable('k32', common + ' --groups 360 --zones 80,80,40', use_mpi=True)
    # executable('k33', common + ' --groups 360 --zones 88,88,44', use_mpi=True)

    # common = 'kripke.exe --arch {arch} --layout {layout} --procs 7,4,4 --niter 1 --legendre 4 --quad 96 --gset 1 '

    # executable('k1',  common + ' --groups 220 --zones 7,4,4',   use_mpi=True)
    # executable('k2',  common + ' --groups 220 --zones 14,8,8', use_mpi=True)
    # executable('k3',  common + ' --groups 220 --zones 21,12,12', use_mpi=True)
    # executable('k4',  common + ' --groups 220 --zones 28,16,16', use_mpi=True)
    # executable('k5',  common + ' --groups 220 --zones 35,20,20', use_mpi=True)
    # executable('k6',  common + ' --groups 220 --zones 42,24,24', use_mpi=True)
    # executable('k7',  common + ' --groups 220 --zones 49,28,28', use_mpi=True)
    # executable('k8',  common + ' --groups 220 --zones 56,32,32', use_mpi=True)
    # executable('k9',  common + ' --groups 220 --zones 63,36,36', use_mpi=True)
    # executable('k10', common + ' --groups 220 --zones 70,40,40', use_mpi=True)
    # executable('k11', common + ' --groups 220 --zones 77,44,44', use_mpi=True)

    # executable('k12', common + ' --groups 320 --zones 7,4,4',    use_mpi=True)
    # executable('k13', common + ' --groups 320 --zones 14,8,8',  use_mpi=True)
    # executable('k14', common + ' --groups 320 --zones 21,12,12', use_mpi=True)
    # executable('k15', common + ' --groups 320 --zones 28,16,16', use_mpi=True)
    # executable('k16', common + ' --groups 320 --zones 35,20,20', use_mpi=True)
    # executable('k17', common + ' --groups 320 --zones 42,24,24', use_mpi=True)
    # executable('k18', common + ' --groups 320 --zones 49,28,28', use_mpi=True)
    # executable('k19', common + ' --groups 320 --zones 56,32,32', use_mpi=True)
    # executable('k20', common + ' --groups 320 --zones 63,36,36', use_mpi=True)
    # executable('k21', common + ' --groups 320 --zones 70,40,40', use_mpi=True)
    # executable('k22', common + ' --groups 320 --zones 77,44,44', use_mpi=True)

    # executable('k23', common + ' --groups 360 --zones 7,4,4',    use_mpi=True)
    # executable('k24', common + ' --groups 360 --zones 14,8,8',  use_mpi=True)
    # executable('k25', common + ' --groups 360 --zones 21,12,12', use_mpi=True)
    # executable('k26', common + ' --groups 360 --zones 28,16,16', use_mpi=True)
    # executable('k27', common + ' --groups 360 --zones 35,20,20', use_mpi=True)
    # executable('k28', common + ' --groups 360 --zones 42,24,24', use_mpi=True)
    # executable('k29', common + ' --groups 360 --zones 49,28,28', use_mpi=True)
    # executable('k30', common + ' --groups 360 --zones 56,32,32', use_mpi=True)
    # executable('k31', common + ' --groups 360 --zones 63,36,36', use_mpi=True)
    # executable('k32', common + ' --groups 360 --zones 70,40,40', use_mpi=True)
    # executable('k33', common + ' --groups 360 --zones 77,44,44', use_mpi=True)

    workload('kripke', executables=[f'k{i}' for i in range(1, 34)])

    workload_variable('ngroups', default='32',
                      description='Number of energy groups. (Default: --groups 32)',
                      workloads=['kripke'])
    workload_variable('lorder', default='4',
                      description='Scattering Legendre Expansion Order (0, 1, ...). (Default: --legendre 4)',
                      workloads=['kripke'])
    workload_variable('nquad', default='96',
                      description='Define the quadrature set to use either a fake S2 with points (ndirs), OR Gauss-Legendre with by points (polar:azim). (Default: --quad 96)',
                      workloads=['kripke'])
    workload_variable('nzx', default='16',
                      description='Number of zones in x. (Default: 16)',
                      workloads=['kripke'])
    workload_variable('nzx', default='16',
                      description='Number of zones in y. (Default: 16)',
                      workloads=['kripke'])
    workload_variable('nzz', default='16',
                      description='Number of zones in z. (Default: 16)',
                      workloads=['kripke'])
    workload_variable('sigt0', default='0.1',
                      description='Total material cross-sections',
                      workloads=['kripke'])
    workload_variable('sigt1', default='0.0001',
                      description='Total material cross-sections',
                      workloads=['kripke'])
    workload_variable('sigt2', default='0.1',
                      description='Total material cross-sections',
                      workloads=['kripke'])
    workload_variable('sigs0', default='0.05',
                      description='Total material cross-sections',
                      workloads=['kripke'])
    workload_variable('sigs1', default='0.00005',
                      description='Total material cross-sections',
                      workloads=['kripke'])
    workload_variable('sigs2', default='0.05',
                      description='Total material cross-sections',
                      workloads=['kripke'])
    workload_variable('arch', default='Sequential',
                      description='Architecture selection. Selects the back-end used for computation, available are Sequential, OpenMP, CUDA and HIP. The default depends on capabilities selected by the build system and is selected from list of increasing precedence: Sequential, OpenMP, CUDA and HIP.',
                      workloads=['kripke'])
    workload_variable('layout', default='ZGD',
                      description='Data layout selection. This determines the data layout and kernel implementation details (such as loop nesting order). The layouts are determined by the order of unknowns in the angular flux: Direction, Group, and Zone. Available layouts are DGZ, DZG, GDZ, GZD, ZDG, and ZGD. The order is specified left-to-right in longest-to-shortest stride. For example: DGZ means that Directions are the longest stride, and Zones are stride-1. (Default: --nest DGZ)',
                      workloads=['kripke'])
#    workload_variable('lout', default='0',
#                      description='Layout of spatial subdomains over mpi ranks. 0 for "Blocked" where local zone sets represent adjacent regions of space. 1 for "Scattered" where adjacent regions of space are distributed to adjacent MPI ranks. (Default: --layout 0)',
#                      workloads=['kripke'])
    workload_variable('npx', default='1',
                      description='Number of MPI ranks in x dimension',
                      workloads=['kripke'])
    workload_variable('npy', default='1',
                      description='Number of MPI ranks in y dimension',
                      workloads=['kripke'])
    workload_variable('npz', default='1',
                      description='Number of MPI ranks in z dimension',
                      workloads=['kripke'])
    workload_variable('ds', default='8',
                      description='Number of direction-sets. Must be a factor of 8, and divide evenly the number of quadrature points. (Default: --dset 8)',
                      workloads=['kripke'])
    workload_variable('gs', default='1',
                      description='Number of energy group-sets. Must divide evenly the number energy groups. (Default: --gset 1)',
                      workloads=['kripke'])
    workload_variable('nzsetx', default='1',
                      description='Number of zone-sets in x',
                      workloads=['kripke'])
    workload_variable('nzsety', default='1',
                      description='Number of zone-sets in y',
                      workloads=['kripke'])
    workload_variable('nzsetz', default='1',
                      description='Number of zone-sets in z',
                      workloads=['kripke'])
    workload_variable('niter', default='10',
                      description='Number of solver iterations to run. (Default: --niter 10)',
                      workloads=['kripke'])
    workload_variable('method', default='sweep',
                      description='Parallel solver method. "sweep" for full up-wind sweep (wavefront algorithm). "bj" for Block Jacobi. (Default: --pmethod sweep)',
                      workloads=['kripke'])

    #figure_of_merit('Figure of Merit (FOM)', log_file='{experiment_run_dir}/{experiment_name}.out', fom_regex=r'Figure of Merit \(FOM\):\s+(?P<fom>[0-9]+\.[0-9]*(e^[0-9]*)?)', group_name='fom', units='')

    #TODO: Fix the FOM success_criteria(...)
    #success_criteria('pass', mode='string', match=r'Figure of Merit \(FOM\)', file='{experiment_run_dir}/{experiment_name}.out')
