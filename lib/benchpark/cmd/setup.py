# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import shutil
import sys

import ruamel.yaml as yaml

import benchpark.paths
from benchpark.debug import debug_print
from benchpark.runtime import RuntimeResources
import benchpark.system


# Note: it would be nice to vendor spack.llnl.util.link_tree, but that
# involves pulling in most of llnl/util/ and spack/util/
def symlink_tree(src, dst, include_fn=None):
    """Like ``cp -R`` but instead of files, create symlinks"""
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)
    # By default, we include all filenames
    include_fn = include_fn or (lambda f: True)
    for x in [src, dst]:
        if not os.path.isdir(x):
            raise ValueError(f"Not a directory: {x}")
    for src_subdir, directories, files in os.walk(src):
        relative_src_dir = pathlib.Path(os.path.relpath(src_subdir, src))
        dst_dir = pathlib.Path(dst) / relative_src_dir
        dst_dir.mkdir(parents=True, exist_ok=True)
        for x in files:
            if not include_fn(x):
                continue
            dst_symlink = dst_dir / x
            src_file = os.path.join(src_subdir, x)
            os.symlink(src_file, dst_symlink)


def setup_parser(root_parser):
    root_parser.add_argument(
        "experiment",
        type=str,
        help="The experiment (benchmark/ProgrammingModel) to run",
    )
    root_parser.add_argument(
        "system", type=str, help="The system on which to run the experiment"
    )
    root_parser.add_argument(
        "experiments_root",
        type=str,
        help="Where to install packages and store results for the experiments. Benchpark expects to manage this directory, and it should be empty/nonexistent the first time you run benchpark setup experiments.",
    )


def command(args):
    """
    experiments_root/
        spack/
        ramble/
        <experiment>/
            <system>/
                workspace/
                    configs/
                        (everything from source/configs/<system>)
                        (everything from source/experiments/<experiment>)
    """

    experiments_root = pathlib.Path(os.path.abspath(args.experiments_root))
    experiment_id = args.experiment
    system_id = args.system
    source_dir = benchpark.paths.benchpark_root

    debug_print(f"source_dir = {source_dir}")
    debug_print(f"specified experiment = {experiment_id}")
    debug_print(f"specified system = {system_id}")

    experiment_src_dir = pathlib.Path(os.path.abspath(str(experiment_id)))
    configs_src_dir = pathlib.Path(os.path.abspath(str(system_id)))
    workspace_dir = experiments_root / str(experiment_id) / str(system_id)

    if workspace_dir.exists():
        if workspace_dir.is_dir():
            print(f"Clearing existing workspace {workspace_dir}")
            shutil.rmtree(workspace_dir)
        else:
            print(
                f"Benchpark expects to manage {workspace_dir} as a directory, but it is not"
            )
            sys.exit(1)

    workspace_dir.mkdir(parents=True)

    ramble_workspace_dir = workspace_dir / "workspace"
    ramble_configs_dir = ramble_workspace_dir / "configs"
    ramble_logs_dir = ramble_workspace_dir / "logs"
    ramble_spack_experiment_configs_dir = (
        ramble_configs_dir / "auxiliary_software_files"
    )

    print(f"Setting up configs for Ramble workspace {ramble_configs_dir}")

    ramble_configs_dir.mkdir(parents=True)
    ramble_logs_dir.mkdir(parents=True)
    ramble_spack_experiment_configs_dir.mkdir(parents=True)

    def include_fn(fname):
        # Only include .yaml files
        # Always exclude files that start with "."
        if fname.startswith("."):
            return False
        if fname.endswith(".yaml"):
            return True
        return False

    symlink_tree(configs_src_dir, ramble_configs_dir, include_fn)
    symlink_tree(experiment_src_dir, ramble_configs_dir, include_fn)
    symlink_tree(
        source_dir / "systems" / "common",
        ramble_spack_experiment_configs_dir,
        include_fn,
    )

    template_name = "execute_experiment.tpl"
    experiment_template_options = [
        configs_src_dir / template_name,
        experiment_src_dir / template_name,
        source_dir / "common-resources" / template_name,
    ]
    for choice_template in experiment_template_options:
        if os.path.exists(choice_template):
            break
    os.symlink(
        choice_template,
        ramble_configs_dir / "execute_experiment.tpl",
    )

    initializer_script = experiments_root / "setup.sh"
    run_script = experiments_root / ".latest-experiment.sh"

    per_workspace_setup = RuntimeResources(experiments_root)

    # Parse experiment YAML for package_manager
    def find(d, tag):
        if tag in d:
            return d[tag]
        for k, v in d.items():
            if isinstance(v, dict):
                result = find(v, tag)
                if result is not None:
                    return result

    with open(str(experiment_src_dir / "ramble.yaml"), "r") as file:
        parsed_yaml = yaml.safe_load(file)
    pkg_manager = find(parsed_yaml, "package_manager")

    pkg_str = ""
    if pkg_manager == "spack":
        spack, first_time_spack = per_workspace_setup.spack_first_time_setup()
        if first_time_spack:
            spack("repo", "add", "--scope=site", f"{source_dir}/repo")

        pkg_str = f"""\
. {per_workspace_setup.spack_location}/share/spack/setup-env.sh

export SPACK_DISABLE_LOCAL_CONFIG=1
"""

    ramble, first_time_ramble = per_workspace_setup.ramble_first_time_setup()
    if first_time_ramble:
        ramble(f"repo add --scope=site {source_dir}/repo")
        ramble('config --scope=site add "config:disable_progress_bar:true"')
        ramble(f"repo add -t modifiers --scope=site {source_dir}/modifiers")
        ramble("config --scope=site add \"config:spack:global:args:'-d'\"")

    if not initializer_script.exists():
        with open(initializer_script, "w") as f:
            f.write(
                f"""\
{pkg_str}
. {per_workspace_setup.ramble_location}/share/ramble/setup-env.sh
"""
            )

    ramble_setup = f"ramble --disable-progress-bar --workspace-dir {ramble_workspace_dir} workspace setup"
    ramble_run = (
        f"ramble --disable-progress-bar --workspace-dir {ramble_workspace_dir} on"
    )

    instructions = f"""\
To complete the benchpark setup, do the following:

    . {initializer_script}

Further steps are needed to build the experiments ({ramble_setup}) and run them ({ramble_run})
"""
    print(instructions)

    # Generate shell script to setup and run latest experiment
    with open(run_script, "w") as f:
        f.write(f"{ramble_setup} && {ramble_run}\n")
