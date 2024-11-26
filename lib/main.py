# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2024 Spack project developers
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import inspect
import os
import pathlib
import shlex
import subprocess
import sys
import yaml

import benchpark.cmd.audit
import benchpark.cmd.system
import benchpark.cmd.experiment
import benchpark.cmd.setup
import benchpark.cmd.unit_test
import benchpark.paths
from benchpark.accounting import (
    benchpark_experiments,
    benchpark_modifiers,
    benchpark_systems,
)


__version__ = "0.1.0"


def main():
    if sys.version_info[:2] < (3, 8):
        raise Exception("Benchpark requires at least python 3.8+.")

    parser = argparse.ArgumentParser(description="Benchpark")
    parser.add_argument(
        "-V", "--version", action="store_true", help="show version number and exit"
    )

    subparsers = parser.add_subparsers(title="Subcommands", dest="subcommand")

    actions = {}
    benchpark_list(subparsers, actions)
    benchpark_tags(subparsers, actions)
    init_commands(subparsers, actions)

    args, unknown_args = parser.parse_known_args()
    no_args = True if len(sys.argv) == 1 else False

    if no_args:
        parser.print_help()
        return 1

    if args.version:
        print(get_version())
        return 0

    if args.subcommand in actions:
        action = actions[args.subcommand]
        if supports_unknown_args(action):
            action(args, unknown_args)
        elif unknown_args:
            raise argparse.ArgumentTypeError(
                f"benchpark {args.subcommand} has no option(s) {unknown_args}"
            )
        else:
            action(args)
    else:
        print(
            "Invalid subcommand ({args.subcommand}) - must choose one of: "
            + " ".join(actions.keys())
        )


def supports_unknown_args(command):
    """Implements really simple argument injection for unknown arguments.

    Commands may add an optional argument called "unknown args" to
    indicate they can handle unknown args, and we'll pass the unknown
    args in.
    """
    info = dict(inspect.getmembers(command))
    varnames = info["__code__"].co_varnames
    argcount = info["__code__"].co_argcount
    return argcount == 2 and varnames[1] == "unknown_args"


def get_version():
    benchpark_version = __version__
    return benchpark_version


def benchpark_list(subparsers, actions_dict):
    list_parser = subparsers.add_parser(
        "list", help="List available experiments, systems, and modifiers"
    )
    list_parser.add_argument("sublist", nargs="?")
    actions_dict["list"] = benchpark_list_handler


def benchpark_benchmarks():
    source_dir = benchpark.paths.benchpark_root
    benchmarks = []
    experiments_dir = source_dir / "legacy" / "experiments"
    for x in os.listdir(experiments_dir):
        benchmarks.append(f"{x}")
    return benchmarks


def benchpark_get_tags():
    f = benchpark.paths.benchpark_root / "tags.yaml"
    tags = []

    with open(f, "r") as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    for k0, v0 in data.items():
        if k0 == "benchpark-tags":
            for k, v in v0.items():
                if isinstance(v, list):
                    for i in v:
                        tags.append(i)
        else:
            print("ERROR file does not contain benchpark-tags")

    return tags


def benchpark_list_handler(args):
    sublist = args.sublist
    benchmarks = benchpark_benchmarks()
    experiments = benchpark_experiments()
    systems = benchpark_systems()
    modifiers = benchpark_modifiers()

    if sublist is None:
        print("Experiments:")
        for experiment in experiments:
            print(f"\t{experiment}")
        print("Systems:")
        for system in systems:
            print(f"\t{system}")
    elif sublist == "benchmarks":
        print("Benchmarks:")
        for benchmark in benchmarks:
            print(f"\t{benchmark}")
    elif sublist == "experiments":
        print("Experiments:")
        for experiment in experiments:
            print(f"\t{experiment}")
    elif sublist == "systems":
        print("Systems:")
        for system in systems:
            print(f"\t{system}")
    elif sublist == "modifiers":
        print("Modifiers:")
        for modifier in modifiers:
            print(f"\t{modifier}")
    else:
        raise ValueError(
            f'Invalid benchpark list "{sublist}" - must choose [experiments], [systems], [modifiers] or leave empty'
        )


def benchpark_check_benchmark(arg_str):
    benchmarks = benchpark_benchmarks()
    found = arg_str in benchmarks
    if not found:
        out_str = f'Invalid benchmark "{arg_str}" - must choose one of: '
        for benchmark in benchmarks:
            out_str += f"\n\t{benchmark}"
        raise ValueError(out_str)
    return found


def benchpark_check_tag(arg_str):
    tags = benchpark_get_tags()
    found = arg_str in tags
    if not found:
        out_str = f'Invalid tag "{arg_str}" - must choose one of: '
        for tag in tags:
            out_str += f"\n\t{tag}"
        raise ValueError(out_str)
    return found


def init_commands(subparsers, actions_dict):
    """This function is for initializing commands that are defined outside
    of this script. It is intended that all command setup will eventually
    be refactored in this way (e.g. `benchpark_setup` will be defined in
    another file.
    """
    system_parser = subparsers.add_parser("system", help="Initialize a system config")
    benchpark.cmd.system.setup_parser(system_parser)

    experiment_parser = subparsers.add_parser(
        "experiment", help="Interact with experiments"
    )
    benchpark.cmd.experiment.setup_parser(experiment_parser)

    setup_parser = subparsers.add_parser(
        "setup", help="Set up an experiment and prepare it to build/run"
    )
    benchpark.cmd.setup.setup_parser(setup_parser)

    unit_test_parser = subparsers.add_parser(
        "unit-test", help="Run benchpark unit tests"
    )
    benchpark.cmd.unit_test.setup_parser(unit_test_parser)

    audit_parser = subparsers.add_parser(
        "audit", help="Look for problems in System/Experiment repos"
    )
    benchpark.cmd.audit.setup_parser(audit_parser)

    actions_dict["system"] = benchpark.cmd.system.command
    actions_dict["experiment"] = benchpark.cmd.experiment.command
    actions_dict["setup"] = benchpark.cmd.setup.command
    actions_dict["unit-test"] = benchpark.cmd.unit_test.command
    actions_dict["audit"] = benchpark.cmd.audit.command


def run_command(command_str, env=None):
    proc = subprocess.Popen(
        shlex.split(command_str),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed command: {command_str}\nOutput: {stdout}\nError: {stderr}"
        )

    return (stdout, stderr)


def benchpark_tags(subparsers, actions_dict):
    create_parser = subparsers.add_parser("tags", help="Tags in Benchpark experiments")
    create_parser.add_argument(
        "experiments_root",
        type=str,
        help="The experiments_root you specified during Benchpark setup.",
    )
    create_parser.add_argument(
        "-a",
        "--application",
        action="store",
        help="The application for which to find Benchpark tags",
    )
    create_parser.add_argument(
        "-t",
        "--tag",
        action="store",
        help="The tag for which to search in Benchpark experiments",
    )
    actions_dict["tags"] = benchpark_tags_handler


def helper_experiments_tags(ramble_exe, benchmarks):
    # find all tags in Ramble applications (both in Ramble built-in and in Benchpark/repo)
    (tags_stdout, tags_stderr) = run_command(f"{ramble_exe} attributes --tags --all")
    ramble_applications_tags = {}
    lines = tags_stdout.splitlines()

    for line in lines:
        key_value = line.split(":")
        ramble_applications_tags[key_value[0]] = key_value[1].strip().split(",")

    benchpark_experiments_tags = {}
    for benchmark in benchmarks:
        if ramble_applications_tags.get(benchmark) is not None:
            benchpark_experiments_tags[benchmark] = ramble_applications_tags[benchmark]

    return benchpark_experiments_tags


def benchpark_tags_handler(args):
    """
    Filter ramble tags by benchpark benchmarks
    """
    experiments_root = pathlib.Path(os.path.abspath(args.experiments_root))
    ramble_location = experiments_root / "ramble"
    ramble_exe = ramble_location / "bin" / "ramble"
    benchmarks = benchpark_benchmarks()

    if args.tag:
        if benchpark_check_tag(args.tag):
            # find all applications in Ramble that have a given tag (both in Ramble built-in and in Benchpark/repo)
            (tag_stdout, tag_stderr) = run_command(f"{ramble_exe} list -t {args.tag}")
            lines = tag_stdout.splitlines()

            for line in lines:
                if line in benchmarks:
                    print(line)

    elif args.application:
        if benchpark_check_benchmark(args.application):
            benchpark_experiments_tags = helper_experiments_tags(ramble_exe, benchmarks)
            if benchpark_experiments_tags.get(args.application) is not None:
                print(benchpark_experiments_tags[args.application])
            else:
                print("Benchmark {} does not exist in ramble.".format(args.application))
    else:
        benchpark_experiments_tags = helper_experiments_tags(ramble_exe, benchmarks)
        print("All tags that exist in Benchpark experiments:")
        for k, v in benchpark_experiments_tags.items():
            print(k)


if __name__ == "__main__":
    main()
