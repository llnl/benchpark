# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import re

from spack.package import *
from spack_repo.builtin.packages.blt.package import Blt as BuiltinBlt


class Blt(BuiltinBlt):

    version("0.7.0", sha256="df8720a9cba1199d21f1d32649cebb9dddf95aa61bc3ac23f6c8a3c6b6083528")