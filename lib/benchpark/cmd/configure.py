# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import yaml

import benchpark.paths


def setup_parser(root_parser):
    root_parser.add_argument(
        "-bl",
        "--bootstrap-location",
        default=None,
        help="Set the path to the bootstrap location",
    )


def command(args):
    data = {}

    if args.bootstrap_location:
        data["bootstrap"] = {
            "location": str(args.bootstrap_location).rstrip("/") + "/.benchpark/",
        }

    print(f"Writing configuration to {benchpark.paths.benchpark_config}")
    with open(benchpark.paths.benchpark_config, "w") as yaml_file:
        yaml.safe_dump(data, yaml_file)
