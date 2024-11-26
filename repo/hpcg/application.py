# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *
from ramble.app.builtin.hpcg import Hpcg as HpcgBase


class Hpcg(HpcgBase):

    tags = ['synthetic',
            'conjugate-gradient','solver','sparse-linear-algebra',
            'large-scale',
            'mpi','network-point-to-point',
            'c++','openmp']
