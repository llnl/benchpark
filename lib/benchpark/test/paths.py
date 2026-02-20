# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from benchpark.paths import paths


def test_benchpark_root(pytestconfig):
    expected_path = pathlib.Path(pytestconfig.inipath).resolve().parent
    assert paths.benchpark_root == expected_path
