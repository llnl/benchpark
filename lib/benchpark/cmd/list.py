# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


import llnl.util.tty.color as color

from benchpark.accounting import (  # noqa: E402
    benchpark_benchmarks,
    benchpark_experiments,
    benchpark_modifiers,
    benchpark_systems,
)


def _print_helper(name, collection):
    name = "@*b" + name + "@."
    strs = ["@*r", "@*c"]
    end = "@."

    color.cprint(name)
    for item in collection:
        if "/" not in item and "+" not in item:
            color.cprint(f"    {strs[0]+item+end}")
        else:
            if "/" in item:
                char = "/"
            else:
                char = "+"
            item = item.split(char)
            color.cprint(f"    {strs[0]+item[0]+end+char+strs[1]+item[1]+end}")


def list_benchmarks(args):
    _print_helper("Benchmarks:", benchpark_benchmarks())


def list_experiments(args):
    _print_helper("Experiments:", benchpark_experiments())


def list_systems(args):
    _print_helper("Systems:", benchpark_systems())


def list_modifiers(args):
    _print_helper("Modifiers:", benchpark_modifiers())


def setup_parser(root_parser):
    list_subparser = root_parser.add_subparsers(
        dest="list_subcommand",
        help="List available experiments, systems, and modifiers",
    )

    benchmarks_parser = list_subparser.add_parser("benchmarks")

    experiments_parser = list_subparser.add_parser("experiments")

    systems_parser = list_subparser.add_parser("systems")

    modifiers_parser = list_subparser.add_parser("modifiers")


def command(args):
    actions = {
        "benchmarks": list_benchmarks,
        "experiments": list_experiments,
        "systems": list_systems,
        "modifiers": list_modifiers,
    }
    if args.list_subcommand in actions:
        actions[args.list_subcommand](args)
    else:
        raise ValueError(f"Unknown subcommand for 'list': {args.list_subcommand}")
