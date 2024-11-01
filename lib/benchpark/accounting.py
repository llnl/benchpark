# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import benchpark.paths


def benchpark_experiments():
    source_dir = benchpark.paths.benchpark_root
    experiments = []
    experiments_dir = source_dir / "legacy" / "experiments"
    for x in os.listdir(experiments_dir):
        for y in os.listdir(experiments_dir / x):
            experiments.append(f"{x}/{y}")
    return experiments


def benchpark_modifiers():
    source_dir = benchpark.paths.benchpark_root
    modifiers = []
    for x in os.listdir(source_dir / "modifiers"):
        modifiers.append(x)
    return modifiers


def benchpark_systems():
    source_dir = benchpark.paths.benchpark_root
    systems = []
    for x in os.listdir(source_dir / "legacy" / "systems"):
        if not (
            os.path.isfile(os.path.join(source_dir / "configs", x)) or x == "common"
        ):
            systems.append(x)
    return systems
