# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
from collections import defaultdict

import benchpark.paths

PROGRAMMING_MODEL_CATEGORY = "programming_model"
SCALING_CATEGORY = "scaling"
EXP_DICT = {
    "OpenMPExperiment": (PROGRAMMING_MODEL_CATEGORY, "openmp"),
    "CudaExperiment": (PROGRAMMING_MODEL_CATEGORY, "cuda"),
    "ROCmExperiment": (PROGRAMMING_MODEL_CATEGORY, "rocm"),
    "MpiOnlyExperiment": (PROGRAMMING_MODEL_CATEGORY, "mpi"),
    "ScalingMode.Strong": (SCALING_CATEGORY, "strong"),
    "ScalingMode.Weak": (SCALING_CATEGORY, "weak"),
    "ScalingMode.Throughput": (SCALING_CATEGORY, "throughput"),
}
SYS_DICT = {
    "OpenMPSystem": "openmp",
    "CudaSystem": "cuda",
    "ROCmSystem": "rocm",
}
MOD_DICT = {
    "Caliper": ("modifier", "caliper"),
}


def benchpark_experiments(exp_dict=EXP_DICT, exclude_variants=[]):
    source_dir = benchpark.paths.benchpark_root
    experiments = []
    experiments_dir = source_dir / "experiments"

    for x in sorted(os.listdir(experiments_dir)):
        if not os.path.isdir(experiments_dir / x):
            continue
        exp_pmodels_scaling = defaultdict(list)
        expr_file = str(experiments_dir) + "/" + x + "/experiment.py"
        if os.path.isfile(expr_file):
            with open(expr_file, "r") as file:
                file_text = file.read()
                for var in exp_dict.keys():
                    if var in file_text and var not in exclude_variants:
                        category, option = exp_dict[var]
                        exp_pmodels_scaling[category].append(option)
        end_str = ""
        for category in [PROGRAMMING_MODEL_CATEGORY, SCALING_CATEGORY]:
            if len(exp_pmodels_scaling[category]) == 0:
                break
            cat_str = "+["
            cat_str += "|".join(exp_pmodels_scaling[category])
            cat_str += "]"
            end_str += cat_str
        experiments.append(x + end_str)
    return experiments


def benchpark_modifiers():
    all_benchmark_modifiers = ["affinity", "allocation", "hwloc"]
    source_dir = benchpark.paths.benchpark_root
    experiments_dir = source_dir / "experiments"
    modifiers = []
    exclude = ["modifier_repo.yaml"]
    for x in sorted(os.listdir(source_dir / "modifiers")):
        check_experiments = True
        if x not in exclude:
            modifiers.append(x)
        if x in all_benchmark_modifiers:
            modifiers.append("\t!(all benchmarks)")
            check_experiments = False
        if check_experiments:
            for exp in sorted(os.listdir(experiments_dir)):
                if not os.path.isdir(experiments_dir / exp):
                    continue
                expr_file = str(experiments_dir) + "/" + exp + "/experiment.py"
                if os.path.isfile(expr_file):
                    with open(expr_file, "r") as file:
                        file_text = file.read()
                        if x in file_text:
                            modifiers.append("\t" + "!" + exp)

    return modifiers


def benchpark_systems(programming_model=None):
    from benchpark.spec import SystemSpec

    source_dir = benchpark.paths.benchpark_root
    systems = []
    exclude = ["all_hardware_descriptions", "common", "repo.yaml"]
    for x in sorted(os.listdir(source_dir / "systems")):
        if x not in exclude and "system.py" in os.listdir(source_dir / "systems" / x):
            system_spec = SystemSpec(x)
            system_class = system_spec.system_class
            # aws uses 'instance_type' not 'cluster'
            cluster_variant = "instance_type" if "aws" in x else "cluster"
            variants = list(system_class.variants.values())
            if len(variants) > 0:
                variants = variants[0]
            clusters = None
            has_clusters = True
            if cluster_variant in variants:
                clusters = list(variants[cluster_variant].values)
            else:
                clusters = [x]
                has_clusters = False
            if programming_model:
                new_clusters = []
                for c in clusters:
                    fullspec = f"{x} {cluster_variant}={c}" if has_clusters else x
                    p_models_list = (
                        SystemSpec(fullspec).concretize().system.programming_models
                    )
                    if any([programming_model == p.name for p in p_models_list]):
                        new_clusters.append(c)
                clusters = new_clusters
            if len(clusters) > 0:
                if has_clusters:
                    systems.append(
                        x + " " + cluster_variant + "=[" + "|".join(clusters) + "]"
                    )
                else:
                    systems.append(x)
    return systems


def benchpark_benchmarks():
    source_dir = benchpark.paths.benchpark_root
    benchmarks = []
    experiments_dir = source_dir / "experiments"
    for x in sorted(os.listdir(experiments_dir)):
        if not os.path.isdir(experiments_dir / x):
            continue
        benchmarks.append(f"{x}")
    return benchmarks
