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


# Note: it would be nice to vendor spack.llnl.util.link_tree, but that
# involves pulling in most of llnl/util/ and spack/util/
def symlink_tree(src, dst, include_fn=None):
    """Like ``cp -R`` but instead of files, create symlinks"""
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)
    if pathlib.Path(src) in pathlib.Path(dst).parents:
        raise Exception(f"Recursive copy from parent to child:\n\t{src}\n\t{dst}")
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
        "experiments_root",
        type=str,
        help="Where to install packages and store results for the experiments. Benchpark expects to manage this directory, and it should be empty/nonexistent the first time you run benchpark setup experiments.",
    )


def determine_experiment_id(exp_src_dir):
    x = pathlib.Path(exp_src_dir)
    for y in x.parents:
        if (y / "system_id.yaml").exists():
            # y is the system dir, we want that and everything after it
            return str(x.relative_to(y.parent))
    raise Exception(
        f"No benchpark system dir detected in {exp_src_dir}"
        " or any parent (no directories containing system_id.yaml)."
    )


_workspace_indicator_file = ".benchpark-ramble-workspace"


def command(args):
    """
    experiments_root/
        spack/
        ramble/
        <experiment root>
            <system>/
                <experiment>/
                    workspace/
                        configs/
                            (everything from source/configs/<system>)
                            (everything from source/experiments/<experiment>)
    """

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

    experiment_src_dir = pathlib.Path(os.path.abspath(str(args.experiment)))

    with open(str(experiment_src_dir / "ramble.yaml"), "r") as file:
        parsed_yaml = yaml.safe_load(file)
    pkg_manager = _find(parsed_yaml, "package_manager")
    system_id = _find(parsed_yaml, "destdir")
    experiment_id = determine_experiment_id(experiment_src_dir)

    debug_print(f"source_dir = {source_dir}")
    debug_print(f"specified system/experiment = {experiment_id}")

    configs_src_dir = pathlib.Path(os.path.abspath(str(system_id)))

    experiments_root = pathlib.Path(os.path.abspath(experiments_root))
    system_id = pathlib.Path(os.path.abspath(system_id))

    workspace_dir = pathlib.Path(experiments_root) / experiment_id

    if workspace_dir.exists():
        if workspace_dir.is_dir():
            if not (workspace_dir / _workspace_indicator_file).exists():
                msg = (
                    f"Derived workspace {workspace_dir} already exists and does not"
                    " appear to have been created by `benchpark setup`. Please choose"
                    " a different directory or clear this dir manually"
                )
                if workspace_dir == pathlib.Path(experiment_src_dir):
                    # if you did `benchpark system init --dest=x/y`
                    # and `benchpark experiment init x/y z`
                    # then for an experiment_root R, `benchpark setup` wants
                    # to make R/y/z (and manage it). Therefore you cannot pick
                    # R=x (note that if you just `benchpark system init --dest=y`
                    # where y is relative, that x is your CWD)
                    msg = (
                        "<experiments_root> cannot be the directory containing"
                        " the `--dest` of `benchpark system init`"
                    )
                msg += (
                    "\n\nIt is recommended to choose a nonexistent directory as the"
                    " <experiments_root> or a directory that has been used as the"
                    " <experiments_root> before"
                )
                print(msg)
                sys.exit(1)
            print(f"Clearing existing workspace {workspace_dir}")
            shutil.rmtree(workspace_dir)
        else:
            print(
                f"Benchpark expects to manage {workspace_dir} as a directory, but it is not"
            )
            sys.exit(1)

    workspace_dir.mkdir(parents=True)
    (workspace_dir / _workspace_indicator_file).touch()

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

    per_workspace_setup = RuntimeResources(
        experiments_root, upstream=RuntimeResources(benchpark.paths.benchpark_home)
    )

    pkg_str = ""
    if pkg_manager == "spack":
        spack_build_stage = experiments_root / "builds"
        spack_user_cache_path = experiments_root / "spack-cache"
        spack, first_time_spack = per_workspace_setup.spack_first_time_setup()
        if first_time_spack:
            site_repos = (
                per_workspace_setup.spack_location / "etc" / "spack" / "repos.yaml"
            )
            with open(site_repos, "w") as f:
                f.write(
                    f"""\
repos::
  benchpark: {source_dir}/repo
  builtin: {per_workspace_setup.pkgs_location}/repos/spack_repo/builtin/
"""
                )
            spack(
                f"config --scope=site add \"config:build_stage:['{spack_build_stage}']\""
            )

        pkg_str = f"""\
export SPACK_USER_CACHE_PATH={spack_user_cache_path}
export SPACK_DISABLE_LOCAL_CONFIG=1
. {per_workspace_setup.spack_location}/share/spack/setup-env.sh
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

    ramble_setup = f"ramble --workspace-dir {ramble_workspace_dir} workspace setup"
    ramble_run = f"ramble --workspace-dir {ramble_workspace_dir} on"

    instructions = f"""\
To complete the benchpark setup, do the following:

    . {initializer_script}

Further steps are needed to build the experiments ({ramble_setup}) and run them ({ramble_run})
"""
    print(instructions)

    # Generate shell script to setup and run latest experiment
    with open(run_script, "w") as f:
        f.write(f"{ramble_setup} && {ramble_run}\n")
