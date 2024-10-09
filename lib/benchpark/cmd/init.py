# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import shutil
import sys

import benchpark.experiment
import benchpark.spec


def init(args):
    # Handle conjoined arguments that argparse doesn't separate
    specs_str = " ".join(args.specs)
    experiment_args, system_args = specs_str.split("--")

    # Parse and concretize system
    system_spec = benchpark.spec.SystemSpec(system_args).concretize()
    system = system_spec.system

    # Parse and concretize experiments
    exp_spec_parser = benchpark.spec.SpecParser(
        benchpark.spec.ExperimentSpec, experiment_args
    )
    experiment_specs = [es.concretize() for es in exp_spec_parser.all_specs()]
    experiments = [es.experiment for es in experiment_specs]

    # Create system directory and print out yaml
    sysdir = os.path.join(args.basedir, system.system_uid())

    try:
        os.mkdir(sysdir)
        system.generate_description(sysdir)
    except FileExistsError:
        print(f"Abort: system dir already exists ({sysdir})")
        sys.exit(1)
    except Exception:
        # If there was a failure, remove any partially-generated resources
        shutil.rmtree(sysdir)
        raise

    # For each experiment, create experiment directory and print out yaml
    for experiment_spec, experiment in zip(experiment_specs, experiments):
        expdir = os.path.join(args.basedir, str(hash(experiment_spec)))

        try:
            os.mkdir(expdir)
            experiment.write_ramble_dict(f"{expdir}/ramble.yaml")
        except FileExistsError:
            print(f"Abort: workload dir already exists ({expdir})")
            sys.exit(1)
        except Exception:
            # If there was a failure, remove any partially-generated resources
            shutil.rmtree(expdir)
            raise


def setup_parser(parser):
    parser.add_argument(
        "--basedir",
        required=True,
        help="Generate a system dir under this, and place all files there",
    )

    parser.add_argument(
        "specs",
        nargs=argparse.REMAINDER,
        metavar="experiment_spec(s) -- system_spec",
        help="Experiment spec(s) and system spec",
    )


def command(args):
    init(args)
