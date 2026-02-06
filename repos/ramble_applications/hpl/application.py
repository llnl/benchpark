# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.app.builtin.hpl import Hpl as HplBase
from ramble.appkit import *


class Hpl(HplBase):

    tags = ['synthetic',
            'blas','solver','dense-linear-algebra',
            'large-scale',
            'mpi','network-collectives','network-point-to-point',
            'c']
