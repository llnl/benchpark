# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import os
import pickle
import shutil
import subprocess
import sys
from pprint import pprint

import llnl.util.tty.color as color
import yaml
from deepdiff import DeepDiff

import benchpark.paths
import benchpark.spec
import benchpark.system


def system_init(args):
    system_spec = benchpark.spec.SystemSpec(" ".join(args.spec)).concretize()
    system_spec.destdir = args.dest
    system = system_spec.system

    if args.basedir:
        base = args.basedir
        sysdir = str(hash(system_spec))
        destdir = os.path.join(base, sysdir)
    elif args.dest:
        destdir = args.dest
    else:
        raise ValueError("Must specify one of: --dest, --basedir")

    try:
        os.makedirs(destdir)
        system.write_system_dict(destdir)
    except FileExistsError:
        print(f"Abort: system description dir already exists ({destdir})")
        sys.exit(1)
    except Exception:
        # If there was a failure, remove any partially-generated resources
        shutil.rmtree(destdir)
        raise

    system_pickle = os.path.join(destdir, "system.pkl")
    with open(system_pickle, "wb") as f:
        pickle.dump(system_spec, f)


def system_id(args):
    temp_sys = benchpark.system.System(args.system_dir)
    data = temp_sys.compute_system_id()
    name = data["system"]["name"]
    spec_hash = data["system"]["config-hash"]
    return f"{name}-{spec_hash[:7]}"


def system_external(args):
    if args.new_system:
        subprocess.run(
            [
                benchpark.paths.benchpark_home / "spack/bin/spack",
                "external",
                "find",
                "--not-buildable",
            ]
        )

        with open(
            benchpark.paths.benchpark_home / "spack/etc/spack/packages.yaml", "r"
        ) as file:
            new_packages = yaml.safe_load(file)["packages"]

        color.cprint("@*rHere are all of the new packages:@.")
        pprint(new_packages)
        return

    system_spec = benchpark.spec.SystemSpec(" ".join(args.spec)).concretize()
    system = system_spec.system

    packages = system.compute_packages_section()["packages"]
    pkg_list = list(packages.keys())
    subprocess.run(
        [
            benchpark.paths.benchpark_home / "spack/bin/spack",
            "external",
            "find",
            "--not-buildable",
        ]
        + [pkg for pkg in pkg_list]
    )

    with open(
        benchpark.paths.benchpark_home / "spack/etc/spack/packages.yaml", "r"
    ) as file:
        new_packages = yaml.safe_load(file)["packages"]

    # Use DeepDiff to find differences
    diff = DeepDiff(
        packages,
        new_packages,
        verbose_level=1,
        ignore_type_in_groups=[(int, str)],
        ignore_string_type_changes=True,
    )

    if not diff:
        color.cprint("@*gNo new packages.@.")
    else:
        color.cprint("@*rThe Packages are different. Here are the differences:@.")
        pprint(diff)
        color.cprint("@*rHere are all of the new packages:@.")
        pprint(new_packages)


def setup_parser(root_parser):
    system_subparser = root_parser.add_subparsers(
        dest="system_subcommand", required=True
    )

    init_parser = system_subparser.add_parser("init")
    init_parser.add_argument("--dest", help="Place all system files here directly")
    init_parser.add_argument(
        "--basedir", help="Generate a system dir under this, and place all files there"
    )

    init_parser.add_argument("spec", nargs="+", help="System spec")

    id_parser = system_subparser.add_parser("id")
    id_parser.add_argument("system_dir")

    external_parser = system_subparser.add_parser(
        "external",
        help='Check packages using "spack external find" for current system against the definitions in benchpark.',
    )
    external_parser.add_argument("spec", nargs="+", help="System spec")
    external_parser.add_argument(
        "--new-system",
        help="Flag if system does not exist in benchpark",
        action="store_true",
    )


def command(args):
    actions = {
        "init": system_init,
        "id": system_id,
        "external": system_external,
    }
    if args.system_subcommand in actions:
        actions[args.system_subcommand](args)
