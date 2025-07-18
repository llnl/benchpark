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
from benchpark.spec import SystemSpec


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
    if name:
        name = "@*b" + name + "@."
        color.cprint(name)

    strs = ["@*r", "@*c"]
    end = "@."

    # Compute filtering
    if filter:
        collection = [item for item in collection if any([f in item for f in filter])]

    for item in collection:
        if "/" not in item and "+" not in item:
            color.cprint(f"    {strs[0]+item+end}")
        else:
            char = "/" if "/" in item else "+"
            item = item.split(char)
            color.cprint(f"    {strs[0]+item[0]+end+char+strs[1]+item[1]+end}")


def list_benchmarks(args):
    _print_helper("Benchmarks:" if not args.no_title else None, benchpark_benchmarks())


def list_experiments(args):
    _print_helper(
        "Experiments:" if not args.no_title else None,
        benchpark_experiments(),
        filter=args.experiment,
    )


def list_systems(args):
    systems = benchpark_systems()
    new_systems = []
    for system in systems:
        sspec, cluster = system.split("/") if "/" in system else (system, None)
        cluster_variant = "instance_type" if "aws" in sspec else "cluster"
        # List of valid programming models for system (MPI assumed to be valid)
        fullspec = sspec if not cluster else f"{sspec} {cluster_variant}={cluster}"
        p_models_list = SystemSpec(fullspec).concretize().system.programming_models
        if not args.programming_model or any(
            [args.programming_model == p.name for p in p_models_list]
        ):
            new_systems.append(fullspec)
    _print_helper("Systems:" if not args.no_title else None, new_systems)


def list_modifiers(args):
    modifiers = benchpark_modifiers() if not args.name else [args.name]
    if args.experiments:
        collection = []
        all_experiments = benchpark_experiments(exclude_variants=[])
        for modifier in modifiers:
            collection.append(modifier)
            exprs = [e.split("+")[0] for e in all_experiments if modifier in e]
            for benchmark in benchpark_benchmarks():
                if any([benchmark == e for e in exprs]):
                    collection.append("\t" + "@*c" + benchmark + "@.")
        _print_helper("Modifiers:" if not args.no_title else None, collection)
    else:
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
        help="Filter systems that support a specific programming model (e.g., 'cuda').",
    )

    modifiers_parser = list_subparser.add_parser("modifiers")
    modifiers_parser.add_argument(
        "--no-title", action="store_true", help="Turn off printing title in output."
    )
    modifiers_parser.add_argument(
        "--experiments",
        "-e",
        action="store_true",
        help="See experiments for modifier, if applicable.",
    )
    modifiers_parser.add_argument(
        "--name", default=None, type=str, help="Optional modifier name"
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
