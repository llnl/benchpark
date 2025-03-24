# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import benchpark.paths
from benchpark.runtime import run_command, working_dir


def show_build_dump(args):
    print("hi")


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
