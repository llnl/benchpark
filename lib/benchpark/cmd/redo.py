# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import pickle
import shutil
import sys

import ruamel.yaml as yaml

import benchpark.paths
from benchpark.debug import debug_print
from benchpark.runtime import RuntimeResources


def setup_parser(root_parser):
    root_parser.add_argument(
        "system",
        type=str,
        help="system dir (containing experiments)",
    )
    root_parser.add_argument(
        "experiments_root",
        type=str,
        help="Where to install packages and store results for the experiments. Benchpark expects to manage this directory, and it should be empty/nonexistent the first time you run benchpark setup experiments.",
    )


def collect_experiments_for_system(system_dir):
    experiments = list()
    for root, _, files in os.walk(system_dir):
        if "ramble.yaml" in files:
            experiments.append(root)
    return experiments


def command(args):
    # Parse experiment YAML for package_manager, system_id
    def _find(d, tag):
        if tag in d:
            return d[tag]
        for k, v in d.items():
            if isinstance(v, dict):
                result = _find(v, tag)
                if result is not None:
                    return result

    experiments_root = pathlib.Path(os.path.abspath(args.experiments_root))
    source_dir = benchpark.paths.benchpark_root

    system_id = args.system
    system_file = os.path.join(system_id, "system.pkl")
    with open(system_file, "rb") as f:
        system_spec = pickle.load(f)

    experiment_dirs = collect_experiments_for_system(system_id)

    for experiment_id in experiment_dirs:
        experiment_src_dir = pathlib.Path(os.path.abspath(str(experiment_id)))

        with open(str(experiment_src_dir / "ramble.yaml"), "r") as file:
            parsed_yaml = yaml.safe_load(file)
        pkg_manager = _find(parsed_yaml, "package_manager")
        system_id = _find(parsed_yaml, "destdir")

        debug_print(f"source_dir = {source_dir}")
        debug_print(f"specified system/experiment = {experiment_id}")

        configs_src_dir = pathlib.Path(os.path.abspath(str(system_id)))

        experiments_root = pathlib.Path(os.path.abspath(experiments_root))
        experiment_id = pathlib.Path(os.path.abspath(experiment_id))
        system_id = pathlib.Path(os.path.abspath(system_id))
        common_root = pathlib.Path(
            os.path.commonpath([experiments_root, experiment_id, system_id])
        )
        workspace_dir = (
            common_root
            / experiments_root.relative_to(common_root)
            / experiment_id.relative_to(common_root)
        )

        experiment_spec = parsed_yaml["ramble"]["config"]["spec"]

    # TODO: at this point you can delete the whole system dir
    # and you can delete each corresponding dir in the experiments_root
    # and then you can rerun system/experiment init; setup
    # To fully clean, you have to remove installs from the spack instance