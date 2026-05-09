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


def _print_helper(name, collection, filter=None):
    """Prints a formatted list of items from a collection with color formatting and optional filtering.

    Args:
        name (str): The title to display above the collection. If None, no title is displayed.
        collection (list of str): A list of strings to display. Items can optionally contain
                                special characters (e.g., '/' or '+') for additional formatting.
        filter (list, optional): A substring to filter the items in the collection.
                                Only items containing this substring will be displayed.
                                If None, all items in the collection are displayed.
    """
    strs = ["@*r", "@*c", "@*m"]
    end = "@."

    if name:
        if isinstance(name, list):
            name = (
                "@*b"
                + name[0]
                + "@."
                + "".join([strs[i - 1] + name[i] + end for i in range(1, len(name))])
            )
        elif isinstance(name, str):
            name = "@*b" + name + "@."
        else:
            raise ValueError(f"'name' is type {type(name)}. Must be list or str.")
        color.cprint(name)

    # Compute filtering
    if filter:
        collection = [item for item in collection if any([f in item for f in filter])]

    for item in collection:
        idx = 0
        if "!" in item:
            item = item.replace("!", "")
            idx = 1
        if "=" not in item and "+" not in item:
            color.cprint(f"    {strs[idx]+item+end}")
        else:
            char = "=" if "=" in item else "+"
            item = item.split(char)
            color.cprint(
                f"    {strs[0]+item[0]+end+char+char.join([strs[i]+item[i]+end for i in range(1,len(item))])}"
            )


def list_benchmarks(args):
    _print_helper("Benchmarks:" if not args.no_title else None, benchpark_benchmarks())


def list_experiments(args):
    _print_helper(
        (
            ["Experiments - ", "BENCHMARK@.+", "PROGRAMMING_MODEL@.+", "SCALING"]
            if not args.no_title
            else None
        ),
        benchpark_experiments(),
        filter=args.experiment,
    )


def list_systems(args):
    _print_helper(
        (
            ["Systems - ", "SYSTEM_DEFINITION", " CLUSTER/INSTANCE"]
            if not args.no_title
            else None
        ),
        benchpark_systems(args.programming_model),
    )


def list_modifiers(args):
    modifiers = benchpark_modifiers()
    if args.hide_benchmarks:
        modifiers = [m for m in modifiers if not m.startswith("\t")]
    _print_helper("Modifiers:" if not args.no_title else None, modifiers)


def setup_parser(root_parser):
    list_subparser = root_parser.add_subparsers(
        dest="list_subcommand",
        help="List available experiments, systems, and modifiers",
        required=True,
    )

    # Add subcommands
    benchmarks_parser = list_subparser.add_parser("benchmarks")
    benchmarks_parser.add_argument(
        "--no-title", action="store_true", help="Turn off printing title in output."
    )

    experiments_parser = list_subparser.add_parser("experiments")
    experiments_parser.add_argument(
        "--experiment",
        "-e",
        type=str,
        nargs="*",
        default=None,
        choices=["cuda", "rocm", "openmp", "strong", "weak", "throughput"],
        help="Filter experiments containing a specific substring (e.g., 'cuda').",
    )
    experiments_parser.add_argument(
        "--no-title", action="store_true", help="Turn off printing title in output."
    )

    systems_parser = list_subparser.add_parser("systems")
    systems_parser.add_argument(
        "--no-title", action="store_true", help="Turn off printing title in output."
    )
    systems_parser.add_argument(
        "--programming-model",
        "-p",
        type=str,
        default=None,
        choices=["cuda", "rocm", "openmp"],
        help="Filter systems that support a specific programming model (e.g., 'cuda').",
    )

    modifiers_parser = list_subparser.add_parser("modifiers")
    modifiers_parser.add_argument(
        "--no-title", action="store_true", help="Turn off printing title in output."
    )
    modifiers_parser.add_argument(
        "--hide-benchmarks",
        action="store_true",
        help="Do not show benchmarks under each modifier in output.",
    )


def command(args):
    actions = {
        "benchmarks": list_benchmarks,
        "experiments": list_experiments,
        "systems": list_systems,
        "modifiers": list_modifiers,
    }
    if args.list_subcommand in actions:
        actions[args.list_subcommand](args)
