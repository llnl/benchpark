# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.app.builtin.hpcc import Hpcc as HpccBase
from ramble.appkit import *


class Hpcc(HpccBase):

    tags = ['synthetic',
            'blas','solver','dense-linear-algebra','fft',
            'large-scale',
            'high-fp','high-memory-bandwidth',
            'regular-memory-access','irregular-memory-access',
            'mpi','network-collectives','network-point-to-point',
            'network-bandwidth-bound','network-bisection-bandwidth-bound',
            'network-latency-bound',
            'c','fortran']
