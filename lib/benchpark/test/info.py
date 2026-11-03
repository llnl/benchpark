# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse

import pytest

import benchpark.cmd.info as info


def _args(subcommand, **kwargs):
    defaults = dict(
        name=None,
        query=None,
        hardware=False,
        maintainers=False,
        variants=False,
        system_site=False,
        spack=False,
        ramble=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(info_subcommand=subcommand, **defaults)


@pytest.mark.parametrize(
    "flag, expected, absent",
    [
        ("hardware", "Hardware", "Maintainers"),
        ("maintainers", "Maintainers", "Hardware"),
        ("variants", "Variants", "Hardware"),
    ],
)
def test_info_system_single_section(capsys, flag, expected, absent):
    info.command(_args("system", name="llnl-cluster", **{flag: True}))

    out = capsys.readouterr().out
    assert f"{expected}:" in out
    assert f"{absent}:" not in out


def test_info_system_shows_every_section_by_default(capsys):
    info.command(_args("system", name="llnl-cluster"))

    out = capsys.readouterr().out
    for section in ("Hardware", "Maintainers", "Variants"):
        assert f"{section}:" in out
    assert "dane" in out


def test_info_experiment_shows_every_section_by_default(capsys):
    info.command(_args("experiment", name=["saxpy"]))

    out = capsys.readouterr().out
    for section in ("Maintainers", "Ramble Name", "Spack Name", "Variants"):
        assert f"{section}:" in out
    assert "    saxpy" in out


def test_info_experiment_single_section(capsys):
    info.command(_args("experiment", name=["saxpy"], maintainers=True))

    out = capsys.readouterr().out
    assert "Maintainers:" in out
    assert "Variants:" not in out


@pytest.mark.parametrize("tool", ["spack", "ramble"])
def test_info_experiment_defers_to_spack_and_ramble(monkeypatch, tool):
    commands = []
    monkeypatch.setattr(info.subprocess, "run", lambda cmd, **kw: commands.append(cmd))

    info.command(_args("experiment", name=["saxpy"], **{tool: True}))

    assert commands == [[tool, "info", "saxpy"]]


def test_info_experiment_requires_programming_model():
    # commbench only supports +cuda or +rocm, so the bare name is incomplete
    with pytest.raises(ValueError, match="must be a valid experiment spec"):
        info.command(_args("experiment", name=["commbench"]))
