# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import benchpark.paths
from benchpark.runtime import RuntimeResources


def setup_parser(root_parser):
    root_parser.add_argument(
        "-l",
        "--location",
        default=benchpark.paths.benchpark_home,
        help="Path to the bootstrap location",
    )


def command(args):
    path = str(Path(args.location).expanduser().resolve()).removesuffix(".benchpark") + "/.benchpark"
    bootstrapper = RuntimeResources(path)
    bootstrapper.bootstrap()
