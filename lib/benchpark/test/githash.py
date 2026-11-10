# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
import subprocess

import pytest

from benchpark.paths import paths


@pytest.fixture
def githash():
    path = paths.benchpark_root / "modifiers" / "githash" / "githash.py"
    spec = importlib.util.spec_from_file_location("githash_script", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _spec_json(version):
    return json.dumps(
        {
            "spec": {
                "nodes": [
                    {
                        "name": "pkg",
                        "version": version,
                        "hash": "pkghash",
                        "parameters": {"commit": f"commit-{version}"},
                        "dependencies": [],
                    }
                ]
            }
        }
    )


def _fake_spack(installed_hashes, calls):
    """Stand-in for subprocess.check_output running spack.

    `spack find` lists `installed_hashes`, or fails when it is None.
    `spack spec /<hash>` returns the installed version, 1.0, and
    `spack spec <name>` the version a fresh concretization picks, 2.0.
    """

    def check_output(args, **kwargs):
        calls.append(args)
        if args[:2] == ["spack", "find"]:
            if installed_hashes is None:
                raise subprocess.CalledProcessError(1, args)
            return "\n".join(installed_hashes) + "\n"
        if args[:3] == ["spack", "spec", "--json"]:
            return _spec_json("1.0" if args[3].startswith("/") else "2.0")
        raise AssertionError(f"unexpected command {args}")

    return check_output


def test_reports_the_installed_spec(githash, monkeypatch):
    calls = []
    monkeypatch.setattr(
        githash.subprocess, "check_output", _fake_spack(["abc123"], calls)
    )

    info = githash.collect_package_info("pkg")

    assert info["application"]["version"] == "1.0"
    assert info["application"]["commit"] == "commit-1.0"
    assert ["spack", "spec", "--json", "/abc123"] in calls


@pytest.mark.parametrize("installed", [None, [], ["abc123", "def456"]])
def test_falls_back_to_the_name(githash, monkeypatch, installed):
    # Not installed, `spack find` failing, or more than one install: query
    # by name as before.
    calls = []
    monkeypatch.setattr(
        githash.subprocess, "check_output", _fake_spack(installed, calls)
    )

    info = githash.collect_package_info("pkg")

    assert info["application"]["version"] == "2.0"
    assert ["spack", "spec", "--json", "pkg"] in calls
