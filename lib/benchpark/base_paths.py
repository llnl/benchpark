# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib


def _source_location() -> pathlib.Path:
    """Return the location of the project source files directory."""
    path_to_this_file = __file__
    return pathlib.Path(path_to_this_file).resolve().parents[2]


_unset = object()


class BasePaths:
    def __init__(self):
        self.benchpark_root = _source_location()
        self.lib_path = self.benchpark_root / "lib" / "benchpark"
        self.test_path = self.lib_path / "test"
        self.hardware_descriptions = (
            self.benchpark_root / "systems" / "all_hardware_descriptions"
        )
        self.checkout_versions = self.benchpark_root / "checkout-versions.yaml"
        self.remote_urls = self.benchpark_root / "remote-urls.yaml"
        self.invocation_working_dir = None
        self.user_input_cfg = _unset


base_paths = BasePaths()


def determine_config_dir():
    """
    Benchpark configs don't merge or override like Spack/Ramble. You
    just point it at a directory and that's where all your config is.
    """
    if base_paths.user_input_cfg is _unset:
        raise Exception("Internal error: config initialization")
    elif base_paths.user_input_cfg:
        if not base_paths.user_input_cfg.exists():
            raise Exception(
                f"Specific config dir does not exist: {base_paths.user_input_cfg}"
            )
        else:
            return base_paths.user_input_cfg

    possible_dirs = [
        base_paths.invocation_working_dir / "benchpark-config",
        base_paths.benchpark_root / "user-config",
        base_paths.benchpark_root / "config",
    ]
    for pd in possible_dirs:
        if pd.exists():
            return pd
