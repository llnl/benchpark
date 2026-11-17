# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import subprocess
import sys

import pytest

import benchpark.cmd.unit_test as unit_test
from benchpark.paths import paths

# A small, fast test module to collect and run in a nested `benchpark unit-test`
TARGET = "lib/benchpark/test/paths.py"


def _unit_test(*args):
    return subprocess.run(
        [sys.executable, str(paths.benchpark_root / "bin/benchpark"), "unit-test"]
        + list(args),
        capture_output=True,
        text=True,
        check=True,
    ).stdout


@pytest.mark.parametrize(
    "flag, expected",
    [
        ("--list", [TARGET]),
        ("--list-long", [f"{TARGET}::", "test_"]),
        ("--list-names", [f"{TARGET}::test_"]),
    ],
)
def test_unit_test_lists_tests(flag, expected):
    out = _unit_test(flag, TARGET)

    for text in expected:
        assert text in out


def test_unit_test_runs_selected_tests():
    out = _unit_test("-k", "test_", "--showlocals", TARGET)

    assert "passed" in out


def test_unit_test_pytest_help():
    assert "usage:" in _unit_test("--pytest-help")


def test_add_back_pytest_args_reassembles_arguments():
    args = argparse.Namespace(
        parsed_args=["-s", "--showlocals"],
        pytest_args=["lib/benchpark/test/paths.py"],
        expression="spec and not slow",
    )

    assert unit_test.add_back_pytest_args(args, ["-x"]) == [
        "-s",
        "--showlocals",
        "-x",
        "lib/benchpark/test/paths.py",
        "-k",
        "spec and not slow",
    ]


def test_add_back_pytest_args_handles_no_arguments():
    args = argparse.Namespace(parsed_args=None, pytest_args=None, expression=None)

    assert unit_test.add_back_pytest_args(args, None) == []
