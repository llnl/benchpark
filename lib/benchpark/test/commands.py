# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import subprocess

import benchpark.paths


def test_list():
    for subcmd in ["experiments", "modifiers", "systems", "benchmarks"]:
        subprocess.run(
            [benchpark.paths.benchpark_root / "bin/benchpark", "list", subcmd], check=True
        )


def test_tags():
    subprocess.run(
        [benchpark.paths.benchpark_root / "bin/benchpark", "tags", "-a", "ad"],
        check=True,
    )
