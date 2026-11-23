#!/usr/bin/env python3
# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Check that the memtrace reader imports with the selected Python paths."""

import sys

sys.path[:0] = sys.argv[1:]

from memtrace import Run  # noqa: F401, E402
