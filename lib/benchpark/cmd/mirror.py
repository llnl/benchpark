# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import os
import os.path
import pathlib
import shutil
import tempfile

import benchpark.paths
from benchpark.runtime import run_command, working_dir


def _dry_run_command(cmd, *args, **kwargs):
    print(cmd)
    if args:
        print(f"\n\t{args}")
    if kwargs:
        print(f"\n\t{kwargs}")


def copytree_part_of(basedir, dest, include):
    def _ignore(dirpath, dirlist):
        if pathlib.Path(dirpath) == pathlib.Path(basedir):
            return sorted(set(dirlist) - set(include))
        else:
            return []

    shutil.copytree(basedir, dest, ignore=_ignore)


def copytree_tracked(basedir, dest):
    tracked = set()
    with working_dir(basedir):
        if not os.path.isdir(os.path.join(basedir, ".git")):
            raise RuntimeError(f"Not a git repo: {basedir}")
        with tempfile.TemporaryDirectory() as tempdir:
            results_path = os.path.join(tempdir, "output.txt")
            with open(results_path, "w") as f:
                run_command("git ls-files", stdout=f)
            with open(results_path, "r") as f:
                for line in f.readlines():
                    tracked.add(pathlib.Path(line.strip()).parts[0])

    tracked = sorted(tracked)
    copytree_part_of(basedir, dest, include=tracked + [".git"])


def locate_benchpark_workspace_parent_of_ramble_workspace(ramble_workspace_dir):
    ramble_workspace = pathlib.Path(ramble_workspace_dir)
    found_parent = None
    for parent in ramble_workspace.parents:
        if {"setup.sh", "spack", "ramble"} <= set(os.listdir(parent)):
            found_parent = parent
            break
    if not found_parent:
        raise RuntimeError(
            "Cannot locate Benchpark workspace as a parent of Ramble workspace"
        )
    return found_parent, ramble_workspace.relative_to(found_parent)


_CACHE_MARKER = ".benchpark-mirror-dir"


def mirror_create(args):
    if args.dry_run:
        global run_command
        run_command = _dry_run_command

    dest = os.path.abspath(args.destdir)
    marker = os.path.join(dest, _CACHE_MARKER)

    ramble_workspace = os.path.abspath(args.workspace)

    workspace, ramble_workspace_relative = (
        locate_benchpark_workspace_parent_of_ramble_workspace(ramble_workspace)
    )
    spack_instance = os.path.join(workspace, "spack")
    ramble_instance = os.path.join(workspace, "ramble")

    if not os.path.isdir(workspace):
        raise RuntimeError(f"{workspace} does not exist")

    if not os.path.exists(dest):
        os.makedirs(dest)
        with open(marker, "w"):
            pass
    elif not os.path.isdir(dest):
        raise RuntimeError(f"{dest} is not a directory")
    elif not os.path.exists(marker):
        raise RuntimeError(
            f"{dest} was not created by `benchpark mirror` (no {marker})"
        )

    cache_storage = os.path.join(dest, "pip-cache")
    ramble_pip_reqs = os.path.join(benchpark.paths.benchpark_root, "requirements.txt")
    if not os.path.exists(cache_storage):
        run_command(f"pip download -r {ramble_pip_reqs} -d {cache_storage}")

    ramble_workspace_dest = os.path.join(dest, ramble_workspace_relative)
    penultimate = pathlib.Path(*pathlib.Path(ramble_workspace_dest).parts[:-1])
    os.makedirs(penultimate, exist_ok=True)

    def _ignore(path, dir_list):
        if pathlib.Path(path) == pathlib.Path(ramble_workspace):
            return ["software"]
        else:
            return []

    if not os.path.exists(ramble_workspace_dest):
        shutil.copytree(ramble_workspace, ramble_workspace_dest, ignore=_ignore)

    spack_dest = os.path.join(dest, "spack")
    if not os.path.exists(spack_dest):
        copytree_tracked(spack_instance, spack_dest)

    ramble_dest = os.path.join(dest, "ramble")
    if not os.path.exists(ramble_dest):
        copytree_tracked(ramble_instance, ramble_dest)

    setup_dest = os.path.join(dest, "setup.sh")
    if not os.path.exists(setup_dest):
        with open(setup_dest, "w", encoding="utf-8") as f:
            f.write(
                """\
if [ -n "${_BENCHPARK_INITIALIZED:-}" ]; then
    return 0
fi

this_script_dir=$(dirname "${BASH_SOURCE[0]}")

. $this_script_dir/spack/share/spack/setup-env.sh
. $this_script_dir/ramble/share/ramble/setup-env.sh

export SPACK_DISABLE_LOCAL_CONFIG=1

export _BENCHPARK_INITIALIZED=true
"""
            )

    ramble_workspace_mirror_dest = os.path.join(dest, "ramble-workspace-mirror")
    if not os.path.exists(ramble_workspace_mirror_dest):
        run_command(
            f"ramble --disable-progress-bar --workspace-dir {ramble_workspace} workspace mirror -d file://{ramble_workspace_mirror_dest}"
        )


def setup_parser(root_parser):
    mirror_subparser = root_parser.add_subparsers(dest="system_subcommand")

    create_parser = mirror_subparser.add_parser("create")
    create_parser.add_argument(
        "--dry-run", action="store_true", default=False, help="For debugging"
    )
    create_parser.add_argument(
        "workspace", help="A benchpark workspace you want to copy"
    )
    create_parser.add_argument("destdir", help="Put all needed resources here")


def command(args):
    actions = {
        "create": mirror_create,
    }
    if args.system_subcommand in actions:
        actions[args.system_subcommand](args)
    else:
        raise ValueError(f"Unknown subcommand for 'system': {args.system_subcommand}")
