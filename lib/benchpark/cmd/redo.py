# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import pickle

import ruamel.yaml as yaml


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

    def strip_system_dir(full_dir):
        full = pathlib.Path(full_dir)
        system = pathlib.Path(system_dir)
        for i, part in enumerate(system.parts):
            assert full.parts[i] == part
        return str(pathlib.Path(*full.parts[len(system.parts) :]))

    experiments = list(strip_system_dir(x) for x in experiments)
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

    system_id = args.system
    system_file = os.path.join(system_id, "system.pkl")
    with open(system_file, "rb") as f:
        system_spec = pickle.load(f)

    experiment_dirs = collect_experiments_for_system(system_id)
    experiments = list()
    setups = list()
    for experiment_id in experiment_dirs:
        experiment_src_dir = pathlib.Path(os.path.abspath(system_id)) / pathlib.Path(
            str(experiment_id)
        )
        with open(str(experiment_src_dir / "ramble.yaml"), "r") as file:
            parsed_yaml = yaml.safe_load(file)

        experiment_spec = parsed_yaml["ramble"]["config"]["spec"]
        experiments.append((experiment_id, experiment_spec))
        setups.append(f"benchpark setup {experiment_src_dir} {experiments_root}")

    reinit_system = f"benchpark system init --dest={system_id} {system_spec}"

    per_experiment = list(
        f'benchpark experiment init --dest={experiment_id} {system_id} "{experiment_spec}"'
        for (experiment_id, experiment_spec) in experiments
    )
    reinit_experiments = "\n".join(per_experiment)

    setups = "\n".join(setups)

    redo_instructions = rf"""
. {experiments_root}/setup.sh
rm -rf {experiments_root}/{system_id}
rm -rf {system_id}
{reinit_system}
{reinit_experiments}
{setups}
"""
    print(redo_instructions)
