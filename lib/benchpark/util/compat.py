# Copyright 2026 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Imports for utilities supplied by Spack or Ramble.

Spack supplies the utilities moved from ``llnl.util`` to ``spack.util``.
Ramble supplies ``HashableMap``, which Spack removed without a replacement.
"""

import spack.util.filesystem as filesystem
import spack.util.tty.colify as colify
import spack.util.tty.color as color
from spack.util.lang import Singleton, dedupe

# Spack removed HashableMap without providing a replacement. Ramble still
# supplies the implementation required by Benchpark's VariantMap.
from llnl.util.lang import HashableMap
