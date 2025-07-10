# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import json
import os
import os.path
import re
import shutil

import benchpark.paths
from benchpark.runtime import run_command


def _find_env_root(basedir):
    for root, _, fnames in os.walk(basedir):
        if "spack.yaml" in fnames:
            return root
    raise Exception(f"Could not find spack.yaml in {basedir}")


def extract_build_commands(log_file):
    extracted = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f.readlines():
            match = re.match(r"^==>\s*\[.*\]\s*(\S.*)", line)
            if not match:
                continue
            extract = match.group(1)
            if any(x in extract for x in ["cmake", "configure", "make"]):
                extracted.append(extract)
    return extracted


def show_build_dump(args):
    env_root = _find_env_root(args.workspace)

    determine_exp = os.path.join(
        benchpark.paths.benchpark_root, "lib", "scripts", "determine-exp.py"
    )
    out, err = run_command(f"spack -e {env_root} python {determine_exp}")
    exp_info = json.loads(out)

    experiment_name = exp_info["root"]

    if not os.path.exists(args.destdir):
        os.mkdir(args.destdir)

    logs_out = os.path.join(args.destdir, f"build-{experiment_name}.log")
    if not os.path.exists(logs_out):
        with open(logs_out, "w") as f:
            run_command(f"spack -e {env_root} logs {experiment_name}", stdout=f)

    build_cmds = extract_build_commands(logs_out)
    cmds_out = os.path.join(args.destdir, f"extracted-commands-{experiment_name}.txt")
    if not os.path.exists(cmds_out):
        with open(cmds_out, "w", encoding="utf-8") as f:
            for cmd in build_cmds:
                f.write(f"{cmd}\n")

    # Spack also stores env vars for the build in the install dir, copy them
    out, err = run_command(f"spack -e {env_root} location -i {experiment_name}")
    install_location = out.strip()
    env_vars_path = os.path.join(install_location, ".spack", "spack-build-env.txt")
    env_vars_out = os.path.join(args.destdir, os.path.basename(f"build-env-{experiment_name}.txt"))
    if not os.path.exists(env_vars_out):
        shutil.copy(env_vars_path, env_vars_out)


def setup_parser(root_parser):
    show_build_subparser = root_parser.add_subparsers(dest="show_build_subcommand")

    dump_parser = show_build_subparser.add_parser("dump")
    dump_parser.add_argument(
        "workspace",
        help="A Ramble workspace you want to want to generate build instructions for",
    )
    dump_parser.add_argument("destdir", help="Put all needed resources here")


def command(args):
    actions = {
        "dump": show_build_dump,
    }
    if args.show_build_subcommand in actions:
        actions[args.show_build_subcommand](args)
    else:
        raise ValueError(
            f"Unknown subcommand for 'show-build': {args.show_build_subcommand}"
        )
