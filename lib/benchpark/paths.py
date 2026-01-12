# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib

import yaml


def _source_location() -> pathlib.Path:
    """Return the location of the project source files directory."""
    path_to_this_file = __file__
    return pathlib.Path(path_to_this_file).resolve().parents[2]


benchpark_root = _source_location()
lib_path = benchpark_root / "lib" / "benchpark"
test_path = lib_path / "test"

benchpark_config = benchpark_root / "configure.yaml"

if benchpark_config.exists():
    with benchpark_config.open("r") as f:
        config = yaml.safe_load(f)
        benchpark_home = config["bootstrap"]["location"]
else:
    benchpark_home = "~/.benchpark"
benchpark_home = pathlib.Path(os.path.expanduser(benchpark_home))


global_ramble_path = benchpark_home / "ramble"
global_spack_path = benchpark_home / "spack"
hardware_descriptions = benchpark_root / "systems" / "all_hardware_descriptions"
checkout_versions = benchpark_root / "checkout-versions.yaml"
remote_urls = benchpark_root / "remote-urls.yaml"
