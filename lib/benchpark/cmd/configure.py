# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

import yaml

import benchpark.config
from benchpark.base_paths import base_paths


def setup_parser(root_parser):
    root_parser.add_argument(
        "-bl",
        "--bootstrap-location",
        default=None,
        help="Set the path to the bootstrap location",
    )


def command(args):
    bootstrap_cfg = benchpark.config.configuration().bootstrap

    if args.bootstrap_location or not bootstrap_cfg.path.exists():
        where = args.bootstrap_location or "~/.benchpark/"
        loc = os.path.expandvars(os.path.expanduser(where))
        bl = str(Path(loc).resolve()).rstrip("/")
        data = {"bootstrap": {"location": bl}}

        # If "user-config" dir has not been created yet (first run), create it
        if (
            bootstrap_cfg.path.resolve()
            == (base_paths.benchpark_root / "config" / "bootstrap.yaml").resolve()
        ):
            user_dir = base_paths.benchpark_root / "user-config"
            os.makedirs(user_dir)
            bootstrap_cfg.path = user_dir / "bootstrap.yaml"
        print(f"Writing configuration to {bootstrap_cfg.path}")
        with open(bootstrap_cfg.path, "w") as yaml_file:
            yaml.safe_dump(data, yaml_file)
