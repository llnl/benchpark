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


def system_init(args):
    system_spec = benchpark.spec.SystemSpec(" ".join(args.spec))
    system_spec = system_spec.concretize()

    system = system_spec.system
    system.initialize()

    if args.basedir:
        base = args.basedir
        sysdir = system.system_uid()
        destdir = os.path.join(base, sysdir)
    elif args.dest:
        destdir = args.dest
    else:
        raise ValueError("Must specify one of: --dest, --basedir")

    try:
        os.mkdir(destdir)
        system.generate_description(destdir)
    except FileExistsError:
        print(f"Abort: system description dir already exists ({destdir})")
        sys.exit(1)
    except Exception:
        # If there was a failure, remove any partially-generated resources
        shutil.rmtree(destdir)
        raise


def system_list(args):
    raise NotImplementedError("'benchpark system list' is not available")


def system_id(args):
    print(benchpark.system.unique_dir_for_description(args.system_dir))


def setup_parser(root_parser):
    system_subparser = root_parser.add_subparsers(dest="system_subcommand")

    init_parser = system_subparser.add_parser("init")
    init_parser.add_argument("--dest", help="Place all system files here directly")
    init_parser.add_argument(
        "--basedir", help="Generate a system dir under this, and place all files there"
    )

    init_parser.add_argument("spec", nargs="+", help="System spec")

    system_subparser.add_parser("list")

    id_parser = system_subparser.add_parser("id")
    id_parser.add_argument("system_dir")


def command(args):
    actions = {
        "init": system_init,
        "list": system_list,
        "id": system_id,
    }
    if args.system_subcommand in actions:
        actions[args.system_subcommand](args)
    else:
        raise ValueError(f"Unknown subcommand for 'system': {args.system_subcommand}")
