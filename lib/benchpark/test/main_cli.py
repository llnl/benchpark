# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for lib/main.py, the `benchpark` command-line entry point."""

import argparse
import shutil
import subprocess
import sys

import pytest
import yaml

import main
from benchpark.paths import paths


def _benchpark(*args):
    return subprocess.run(
        [sys.executable, str(paths.benchpark_root / "bin/benchpark")] + list(args),
        capture_output=True,
        text=True,
        check=True,
    ).stdout


@pytest.mark.parametrize("args", [["--version"], ["-V"]])
def test_version_exits_before_bootstrapping(args):
    assert _benchpark(*args).strip() == main.__version__


@pytest.mark.parametrize("args", [[], ["-h"], ["--help"]])
def test_help(args):
    assert _benchpark(*args).startswith("usage: benchpark")


def test_configure_writes_bootstrap_location(tmp_path):
    config_dir = tmp_path / "config"
    shutil.copytree(paths.benchpark_root / "config", config_dir)
    location = tmp_path / "bootstrap"

    out = _benchpark(
        f"--config={config_dir}", "configure", "--bootstrap-location", str(location)
    )

    assert f"Writing configuration to {config_dir / 'bootstrap.yaml'}" in out
    written = yaml.safe_load((config_dir / "bootstrap.yaml").read_text())
    assert written == {"bootstrap": {"location": str(location.resolve())}}


def test_main_without_subcommand_prints_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["benchpark"])

    assert main.main() == 1
    assert "usage:" in capsys.readouterr().out


def test_main_rejects_unknown_option(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["benchpark", "list", "experiments", "--no-such-option"]
    )

    with pytest.raises(argparse.ArgumentTypeError, match="--no-such-option"):
        main.main()


def test_main_reports_missing_subcommand(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["benchpark", "-C", str(paths.benchpark_root)])

    assert main.main() == 0
    assert "Invalid subcommand" in capsys.readouterr().out


def test_run_command_returns_output_and_raises_on_failure():
    assert main.run_command("echo hello") == ("hello\n", "")
    with pytest.raises(RuntimeError, match="Failed command: false"):
        main.run_command("false")


def test_tags_come_from_taxonomy():
    tags = main.benchpark_get_tags()

    assert "asc" in tags and "cfd" in tags
    assert main.benchpark_check_tag("cfd")
    with pytest.raises(ValueError, match='Invalid tag "not-a-tag"'):
        main.benchpark_check_tag("not-a-tag")


def test_check_benchmark():
    assert main.benchpark_check_benchmark("kripke")
    with pytest.raises(ValueError, match='Invalid benchmark "not-a-benchmark"'):
        main.benchpark_check_benchmark("not-a-benchmark")


@pytest.fixture
def fake_ramble(monkeypatch):
    """Replace the ramble invocations made by `benchpark tags`."""
    commands = []

    def fake_run_command(command, env=None):
        commands.append(command)
        if command.endswith("attributes --tags --all"):
            return "kripke: asc,cfd\nnot-a-benchpark-app: cfd\n", ""
        if " list -t " in command:
            return "kripke\nnot-a-benchpark-app\n", ""
        raise AssertionError(command)

    monkeypatch.setattr(main, "run_command", fake_run_command)
    monkeypatch.setattr(main.subprocess, "run", lambda cmd, **kw: commands.append(cmd))
    return commands


def _tags_args(tag=None, application=None):
    return argparse.Namespace(tag=tag, application=application)


def test_tags_filters_applications_by_tag(fake_ramble, capsys):
    main.benchpark_tags_handler(_tags_args(tag="cfd"))

    # Only Benchpark benchmarks are reported, not every Ramble application
    assert capsys.readouterr().out.splitlines() == ["kripke"]
    assert fake_ramble[0][1:3] == ["repo", "add"]


def test_tags_for_application(fake_ramble, capsys):
    main.benchpark_tags_handler(_tags_args(application="kripke"))

    assert capsys.readouterr().out.strip() == "['asc', 'cfd']"


def test_tags_for_application_without_ramble_tags(fake_ramble, capsys):
    main.benchpark_tags_handler(_tags_args(application="amg2023"))

    assert "Benchmark amg2023 does not exist in ramble." in capsys.readouterr().out


def test_tags_lists_tagged_benchmarks_by_default(fake_ramble, capsys):
    main.benchpark_tags_handler(_tags_args())

    assert capsys.readouterr().out.splitlines() == [
        "All tags that exist in Benchpark experiments:",
        "kripke",
    ]
