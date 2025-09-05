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


def collect_experiments(workspace_dir):
    experiments = list()
    for dirpath, dirnames, filenames in os.walk(workspace_dir):
        for fname in filenames:
            if fname == "execute_experiment":
                experiments.append(os.path.join(dirpath, fname))
    return experiments


def show_build_dump(args):
    env_root = _find_env_root(args.workspace)

    determine_exp = os.path.join(
        benchpark.paths.benchpark_root, "lib", "scripts", "experiment-build-info.py"
    )
    out, err = run_command(f"spack -e {env_root} python {determine_exp}")
    exp_info = json.loads(out)

    root_name = exp_info["root"]

    urls = exp_info["urls"]

    if not os.path.exists(args.destdir):
        os.mkdir(args.destdir)

    url_info = os.path.join(args.destdir, "url-info.txt")
    if not os.path.exists(url_info):
        with open(url_info, "w") as f:
            for pkg_name, info in urls.items():
                url = info["url"]
                details = info["details"]
                f.write(f"{pkg_name} ({url}): {str(details)}\n")

    tree = os.path.join(args.destdir, f"{root_name}-tree.txt")
    if not os.path.exists(tree):
        with open(tree, "w") as f:
            f.write(exp_info["tree"])

    root_run_vars_file = os.path.join(args.destdir, f"{root_name}-run-vars.txt")
    with open(root_run_vars_file, "w") as f:
        run_command(f"spack -e {env_root} load --sh {root_name}", stdout=f)

    if args.download:
        out_mirror = os.path.join(args.destdir, "source-downloads")
        run_command(f"spack -e {env_root} mirror create -d {out_mirror} --all")

    for pkg_name, build_env_file in exp_info["info"]:
        logs_out = os.path.join(args.destdir, f"{pkg_name}-build.log")
        if not os.path.exists(logs_out):
            with open(logs_out, "w") as f:
                run_command(f"spack -e {env_root} logs {pkg_name}", stdout=f)

        build_cmds = extract_build_commands(logs_out)
        cmds_out = os.path.join(args.destdir, f"{pkg_name}-extracted-commands.txt")
        if not os.path.exists(cmds_out):
            with open(cmds_out, "w", encoding="utf-8") as f:
                for cmd in build_cmds:
                    f.write(f"{cmd}\n")

        env_vars_out = os.path.join(
            args.destdir, os.path.basename(f"{pkg_name}-build-env.txt")
        )
        if not os.path.exists(env_vars_out):
            shutil.copy(build_env_file, env_vars_out)

    for i, exp in enumerate(collect_experiments(args.workspace)):
        exp_out = os.path.join(args.destdir, f"exp-{i}")
        if not os.path.exists(exp_out):
            shutil.copy(exp, exp_out)


def setup_parser(root_parser):
    show_build_subparser = root_parser.add_subparsers(
        dest="show_build_subcommand", required=True
    )

    dump_parser = show_build_subparser.add_parser("dump")
    dump_parser.add_argument(
        "--download", action="store_true", help="Download the associated sources"
    )
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
