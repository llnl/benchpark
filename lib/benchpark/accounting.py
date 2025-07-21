# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import benchpark.paths
import benchpark.spec

exclude_exper = ["repo.yaml"]
exp_dict = {
    "OpenMPExperiment": "openmp",
    "CudaExperiment": "cuda",
    "ROCmExperiment": "rocm",
    "SingleNode": "single_node",
    "StrongScaling": "strong",
    "ThroughputScaling": "throughput",
    "WeakScaling": "weak",
    "Caliper": "caliper",
    "ScalingMode.Strong": "scaling=strong",
    "ScalingMode.Weak": "scaling=weak",
    "ScalingMode.Throughput": "scaling=throughput",
}
sys_dict = {
    "OpenMPSystem": "openmp",
    "CudaSystem": "cuda",
    "ROCmSystem": "rocm",
}
non_experiments = ["Caliper", "Affinity"]


def benchpark_experiments(exclude_variants=non_experiments):
    source_dir = benchpark.paths.benchpark_root
    experiments = []
    experiments_dir = source_dir / "experiments"

    for x in sorted(os.listdir(experiments_dir)):
        if x not in exclude_exper:
            expr_file = str(experiments_dir) + "/" + x + "/experiment.py"
            if os.path.isfile(expr_file):
                with open(expr_file, "r") as file:
                    file_text = file.read()
                    experiments.append(x)  # default expr
                    for var in exp_dict.keys():
                        if var in file_text and var not in exclude_variants:
                            if "=" in exp_dict[var]:
                                joiner = " "
                            else:
                                joiner = "+"
                            experiments.append(f"{x}{joiner}{exp_dict[var]}")
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
    exclude = ["all_hardware_descriptions", "common", "repo.yaml"]
    for x in sorted(os.listdir(source_dir / "systems")):
        if x not in exclude and "system.py" in os.listdir(source_dir / "systems" / x):
            system_spec = benchpark.spec.SystemSpec(x)
            system_class = system_spec.system_class
            # aws uses 'instance_type' not 'cluster'
            cluster_variant = "instance_type" if "aws" in x else "cluster"
            variants = list(system_class.variants.values())
            if len(variants) > 0:
                variants = variants[0]
            clusters = None
            if cluster_variant in variants:
                clusters = list(variants[cluster_variant].values)
            if clusters:
                for c in clusters:
                    systems.append(x + "/" + c)
            else:
                systems.append(x)
    return systems


def benchpark_benchmarks():
    source_dir = benchpark.paths.benchpark_root
    benchmarks = []
    experiments_dir = source_dir / "experiments"
    for x in sorted(os.listdir(experiments_dir)):
        if x not in exclude_exper:
            benchmarks.append(f"{x}")
    return benchmarks
