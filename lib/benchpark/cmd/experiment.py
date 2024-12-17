# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import sys

import benchpark.experiment
import benchpark.spec


def experiment_init(args):
    experiment_spec = benchpark.spec.ExperimentSpec(" ".join(args.spec)).concretize()
    experiment = experiment_spec.experiment

    if args.basedir:
        base = args.basedir
        expdir = str(hash(experiment_spec))
        destdir = os.path.join(base, expdir)
    elif args.dest:
        destdir = args.dest
    else:
        raise ValueError("Must specify one of: --dest, --basedir")

    try:
        os.mkdir(destdir)
        experiment.write_ramble_dict(f"{destdir}/ramble.yaml")
    except FileExistsError:
        print(f"Abort: experiment description dir already exists ({destdir})")
        sys.exit(1)
    except Exception:
        # If there was a failure, remove any partially-generated resources
        shutil.rmtree(destdir)
        raise


def experiment_list(args):
    experiments = benchpark.repo.all_object_names(
        benchpark.repo.ObjectTypes.experiments
    )
    # TODO: prettier printing
    print("    ".join(experiments))


def setup_parser(root_parser):
    system_subparser = root_parser.add_subparsers(dest="experiment_subcommand")

    init_parser = system_subparser.add_parser("init")
    init_parser.add_argument("--dest", help="Place all system files here directly")
    init_parser.add_argument(
        "--basedir", help="Generate a system dir under this, and place all files there"
    )

    init_parser.add_argument("spec", nargs="+", help="Experiment spec")

    system_subparser.add_parser("list")


def command(args):
    actions = {
        "init": experiment_init,
        "list": experiment_list,
    }
    if args.experiment_subcommand in actions:
        actions[args.experiment_subcommand](args)
    else:
        raise ValueError(
            f"Unknown subcommand for 'experiment': {args.experiment_subcommand}"
        )
