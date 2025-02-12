# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import os
import os.path
import shutil
import sys
import tempfile

import benchpark.paths
from bnechpark.runtime import run_command

def copy_git_repo_exclude_untracked(git_repo_location, dst_archive_path)
    with tempfile.TemporaryDirectory() as tempdir:
        file_list = os.path.join(tempdir, "repo_list.txt")
        with open(file_list, "w") as f:
            run_command(f"git ls-files -c -m {git_repo_location", output=f)

        run_command("tar -cf {dst_archive_path} -T {file_list}")


def mirror_create(args):
    ramble_pip_reqs = os.path.join(benchpark.paths.benchpark_root, "requirements.txt")


def setup_parser(root_parser):
    mirror_subparser = root_parser.add_subparsers(dest="system_subcommand")

    create_parser = mirror_subparser.add_parser("create")
    create_parser.add_argument("workspace", help="A benchpark workspace you want to copy")


def command(args):
    actions = {
        "create": mirror_create,
    }
    if args.system_subcommand in actions:
        actions[args.system_subcommand](args)
    else:
        raise ValueError(f"Unknown subcommand for 'system': {args.system_subcommand}")
