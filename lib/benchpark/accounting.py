# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import benchpark.paths

exclude_exper = ["repo.yaml"]


def benchpark_experiments():
    source_dir = benchpark.paths.benchpark_root
    experiments = []
    experiments_dir = source_dir / "experiments"
    exclude_variants = ["Caliper"]
    for x in sorted(os.listdir(experiments_dir)):
        if x not in exclude_exper:
            experiment_spec = benchpark.spec.ExperimentSpec(x)
            conc = experiment_spec.concretize()
            experiment_class = conc.experiment
            for h in experiment_class.__dict__["helpers"]:
                variant = str(h).split(".")[2]
                if variant not in exclude_variants:
                    experiments.append(f"{x}/{variant}")
    return experiments


def benchpark_modifiers():
    source_dir = benchpark.paths.benchpark_root
    modifiers = []
    exclude = ["modifier_repo.yaml"]
    for x in sorted(os.listdir(source_dir / "modifiers")):
        if x not in exclude:
            modifiers.append(x)

    return modifiers


def benchpark_systems():
    source_dir = benchpark.paths.benchpark_root
    systems = []
    exclude = ["all_hardware_descriptions", "repo.yaml"]
    for x in sorted(os.listdir(source_dir / "systems")):
        if x not in exclude:
            systems.append(x+":")
            system_spec = benchpark.spec.SystemSpec(x)
            system_class = system_spec.system_class
            for c in system_class.id_to_resources.keys():
                systems.append("    "+c)
    return systems


def benchpark_benchmarks():
    source_dir = benchpark.paths.benchpark_root
    benchmarks = []
    experiments_dir = source_dir / "experiments"
    for x in sorted(os.listdir(experiments_dir)):
        if x not in exclude_exper:
            benchmarks.append(f"{x}")
    return benchmarks
