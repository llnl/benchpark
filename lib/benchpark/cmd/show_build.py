# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import os
import os.path

import benchpark.paths
from benchpark.runtime import run_command, working_dir


def _find_env_root(basedir):
    for root, _, fnames in os.walk(basedir):
        if "spack.yaml" in fnames:
            return root
    raise Exception(f"Could not find spack.yaml in {basedir}")


def show_build_dump(args):
    env_root = _find_env_root(args.workspace)

    determine_exp = os.path.join(benchpark.paths.benchpark_root, "lib", "scripts", "determine-exp.py")
    out, err = run_command(f"spack -e {env_root} python {determine_exp}")
    experiment_name = out.strip()

    logs_out = os.path.join(args.destdir, f"build-{experiment_name}.log")
    if os.path.exists(logs_out):
        raise Exception(f"Output file already exists: {logs_out}")
    with open(logs_out, "w") as f:
        run_command(f"spack -e {env_root} logs {experiment_name}", stdout=f)


def setup_parser(root_parser):
    show_build_subparser = root_parser.add_subparsers(dest="show_build_subcommand")

    dump_parser = show_build_subparser.add_parser("dump")
    dump_parser.add_argument(
        "workspace", help="A Ramble workspace you want to want to generate build instructions for"
    )
    dump_parser.add_argument("destdir", help="Put all needed resources here")


def command(args):
    actions = {
        "dump": show_build_dump,
    }
    if args.show_build_subcommand in actions:
        actions[args.show_build_subcommand](args)
    else:
        raise ValueError(f"Unknown subcommand for 'show-build': {args.show_build_subcommand}")
