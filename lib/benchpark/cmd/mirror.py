# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import sys

import benchpark.system
import benchpark.spec


def mirror_create(args):
    print("hi")

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
