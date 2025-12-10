# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2024 Spack project developers
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import inspect
import shlex
import subprocess
import sys

import yaml

__version__ = "0.1.0"
if "-V" in sys.argv or "--version" in sys.argv:
    print(__version__)
    exit()
helpstr = """usage: main.py [-h] [-V] {tags,system,experiment,setup,unit-test,audit,mirror,info,show-build,list,bootstrap,analyze,configure} ...

Benchpark

options:
  -h, --help            show this help message and exit
  -V, --version         show version number and exit

Subcommands:
  {tags,system,experiment,setup,unit-test,audit,mirror,info,show-build,list,bootstrap,analyze,configure}
    tags                Tags in Benchpark experiments
    system              Initialize a system config
    experiment          Interact with experiments
    setup               Set up an experiment and prepare it to build/run
    unit-test           Run benchpark unit tests
    audit               Look for problems in System/Experiment repos
    mirror              Copy a benchpark workspace
    info                Get information about Systems and Experiments
    show-build          Show how spack built a benchmark
    list                List experiments, systems, benchmarks, and modifiers
    bootstrap           Bootstrap benchpark or update an existing bootstrap
    analyze             Perform pre-defined analysis on the performance data (caliper files) after 'ramble on'
    configure           Configure options relating to the Benchpark environment
    """
if len(sys.argv) == 1 or "-h" == sys.argv[1] or "--help" == sys.argv[1]:
    print(helpstr)
    exit()

import benchpark.paths  # noqa: E402
from benchpark.runtime import RuntimeResources  # noqa: E402

if sys.argv[1] == "configure":
    import benchpark.cmd.configure  # noqa: E402

    parser = argparse.ArgumentParser(description="Benchpark")
    subparsers = parser.add_subparsers(title="Subcommands", dest="subcommand")
    configure_parser = subparsers.add_parser(
        "configure", help="Configure options relating to the Benchpark environment"
    )
    benchpark.cmd.configure.setup_parser(configure_parser)
    args = parser.parse_args()
    benchpark.cmd.configure.command(args)
    sys.exit(0)

bootstrapper = RuntimeResources(benchpark.paths.benchpark_home)  # noqa
bootstrapper.bootstrap()  # noqa

import benchpark.cmd.audit  # noqa: E402
import benchpark.cmd.bootstrap  # noqa: E402
import benchpark.cmd.experiment  # noqa: E402
import benchpark.cmd.info  # noqa: E402
import benchpark.cmd.list  # noqa: E402
import benchpark.cmd.mirror  # noqa: E402
import benchpark.cmd.redo  # noqa: E402
import benchpark.cmd.setup  # noqa: E402
import benchpark.cmd.show_build  # noqa: E402
import benchpark.cmd.system  # noqa: E402
import benchpark.cmd.unit_test  # noqa: E402
from benchpark.accounting import benchpark_benchmarks  # noqa: E402

try:
    import benchpark.cmd.analyze  # noqa: E402

    analyze_installed = True
except ModuleNotFoundError:
    analyze_installed = False


def main():
    if sys.version_info[:2] < (3, 8):
        raise Exception("Benchpark requires at least python 3.8+.")

    parser = argparse.ArgumentParser(description="Benchpark")
    parser.add_argument(
        "-V", "--version", action="store_true", help="show version number and exit"
    )

    subparsers = parser.add_subparsers(title="Subcommands", dest="subcommand")

    actions = {}
    benchpark_tags(subparsers, actions)
    init_commands(subparsers, actions)

    args, unknown_args = parser.parse_known_args()
    no_args = True if len(sys.argv) == 1 else False

    if no_args:
        parser.print_help()
        return 1

    exit_code = 0

    if args.subcommand in actions:
        action = actions[args.subcommand]
        if supports_unknown_args(action):
            exit_code = action(args, unknown_args)
        elif unknown_args:
            raise argparse.ArgumentTypeError(
                f"benchpark {args.subcommand} has no option(s) {unknown_args}"
            )
        else:
            exit_code = action(args)
    else:
        print(
            "Invalid subcommand ({args.subcommand}) - must choose one of: "
            + " ".join(actions.keys())
        )
    return exit_code


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


def benchpark_get_tags():
    f = benchpark.paths.benchpark_root / "taxonomy.yaml"
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

    mirror_parser = subparsers.add_parser("mirror", help="Copy a benchpark workspace")
    benchpark.cmd.mirror.setup_parser(mirror_parser)

    info_parser = subparsers.add_parser(
        "info", help="Get information about Systems and Experiments"
    )
    benchpark.cmd.info.setup_parser(info_parser)

    show_build_parser = subparsers.add_parser(
        "show-build", help="Show how spack built a benchmark"
    )
    benchpark.cmd.show_build.setup_parser(show_build_parser)

    list_parser = subparsers.add_parser(
        "list", help="List experiments, systems, benchmarks, and modifiers"
    )
    benchpark.cmd.list.setup_parser(list_parser)

    bootstrap_parser = subparsers.add_parser(
        "bootstrap", help="Bootstrap benchpark or update an existing bootstrap"
    )
    benchpark.cmd.bootstrap.setup_parser(bootstrap_parser)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Perform pre-defined analysis on the performance data (caliper files) after 'ramble on'",
    )

    redo_parser = subparsers.add_parser(
        "redo", help="Re-instantiate all experiments in a system"
    )
    benchpark.cmd.redo.setup_parser(redo_parser)

    actions_dict["system"] = benchpark.cmd.system.command
    actions_dict["experiment"] = benchpark.cmd.experiment.command
    actions_dict["setup"] = benchpark.cmd.setup.command
    actions_dict["unit-test"] = benchpark.cmd.unit_test.command
    actions_dict["audit"] = benchpark.cmd.audit.command
    actions_dict["mirror"] = benchpark.cmd.mirror.command
    actions_dict["info"] = benchpark.cmd.info.command
    actions_dict["show-build"] = benchpark.cmd.show_build.command
    actions_dict["list"] = benchpark.cmd.list.command
    actions_dict["bootstrap"] = benchpark.cmd.bootstrap.command
    actions_dict["redo"] = benchpark.cmd.redo.command
    if analyze_installed:
        benchpark.cmd.analyze.setup_parser(analyze_parser)
        actions_dict["analyze"] = benchpark.cmd.analyze.command
    else:

        def analyze_command_placeholder(args, unknown_args):
            raise RuntimeError(
                "Packages required for 'benchpark analyze' not found. run 'pip install .[analyze]' from the 'benchpark' directory."
            )

        actions_dict["analyze"] = analyze_command_placeholder


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
    source_dir = benchpark.paths.benchpark_root
    ramble_exe = benchpark.paths.benchpark_home / "ramble/bin/ramble"
    subprocess.run([ramble_exe, "repo", "add", "--scope=site", f"{source_dir}/repo"])
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
    exit_code = main()
    if exit_code is not None and isinstance(exit_code, int):
        sys.exit(exit_code)
