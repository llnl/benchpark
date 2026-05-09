# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.app.builtin.md_test import MdTest as MdTestBase
from ramble.appkit import *


class MdTest(MdTestBase):

    tags = ['synthetic','i-o','large-scale','mpi','c']
