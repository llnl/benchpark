# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import json

import pytest

import benchpark.cmd.show_build as show_build

BUILD_LOG = """\
==> [2026-01-01-10:00:00.000001] Installing saxpy
==> [2026-01-01-10:00:01.000002] 'cmake' '-G' 'Unix Makefiles' '../src'
==> [2026-01-01-10:00:02.000003] 'make' '-j8'
==> [2026-01-01-10:00:03.000004] 'make' '-j8' 'install'
plain output that is not a Spack message
==> Not a timestamped command: make
"""


@pytest.fixture
def ramble_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "software" / "saxpy").mkdir(parents=True)
    (workspace / "software" / "saxpy" / "spack.yaml").write_text("spack: {}\n")
    for exp in ("saxpy_1", "saxpy_2"):
        (workspace / "experiments" / exp).mkdir(parents=True)
        (workspace / "experiments" / exp / "execute_experiment").write_text(exp)
    build_env = tmp_path / "spack-build-env.txt"
    build_env.write_text("export CC=gcc\n")
    return workspace, build_env


@pytest.fixture
def fake_spack(monkeypatch, ramble_workspace):
    workspace, build_env = ramble_workspace
    calls = []
    exp_info = {
        "root": "saxpy",
        "urls": {"saxpy": {"url": "https://example.com/saxpy.tgz", "details": "1.0"}},
        "tree": "saxpy@1.0\n    ^cmake@3.30\n",
        "info": [["saxpy", str(build_env)]],
    }

    def fake_run_command(command, stdout=None, **kwargs):
        calls.append(command)
        if "experiment-build-info.py" in command:
            return json.dumps(exp_info), ""
        if " load --sh " in command:
            stdout.write("export PATH=/opt/saxpy/bin:$PATH\n")
        elif " logs " in command:
            stdout.write(BUILD_LOG)
        return "", ""

    monkeypatch.setattr(show_build, "run_command", fake_run_command)
    return calls


def _args(workspace, destdir, download=False):
    return argparse.Namespace(
        show_build_subcommand="dump",
        workspace=str(workspace),
        destdir=str(destdir),
        download=download,
    )


def test_show_build_dump_collects_build_information(
    ramble_workspace, fake_spack, tmp_path
):
    workspace, _ = ramble_workspace
    dest = tmp_path / "dump"

    show_build.command(_args(workspace, dest))

    env_root = workspace / "software" / "saxpy"
    assert fake_spack[0].startswith(f"spack -e {env_root} python ")
    assert f"spack -e {env_root} load --sh saxpy" in fake_spack
    assert f"spack -e {env_root} logs saxpy" in fake_spack
    assert not any(" mirror create " in c for c in fake_spack)

    assert (dest / "url-info.txt").read_text() == (
        "saxpy (https://example.com/saxpy.tgz): 1.0\n"
    )
    assert (dest / "saxpy-tree.txt").read_text().startswith("saxpy@1.0")
    assert "/opt/saxpy/bin" in (dest / "saxpy-run-vars.txt").read_text()
    assert (dest / "saxpy-build.log").read_text() == BUILD_LOG
    assert (dest / "saxpy-extracted-commands.txt").read_text().splitlines() == [
        "'cmake' '-G' 'Unix Makefiles' '../src'",
        "'make' '-j8'",
        "'make' '-j8' 'install'",
    ]
    assert (dest / "saxpy-build-env.txt").read_text() == "export CC=gcc\n"
    copied = sorted((dest / name).read_text() for name in ("exp-0", "exp-1"))
    assert copied == ["saxpy_1", "saxpy_2"]


def test_show_build_dump_download_and_rerun(ramble_workspace, fake_spack, tmp_path):
    workspace, _ = ramble_workspace
    dest = tmp_path / "dump"
    dest.mkdir()
    (dest / "url-info.txt").write_text("kept\n")
    (dest / "saxpy-build.log").write_text(BUILD_LOG)

    show_build.command(_args(workspace, dest, download=True))

    env_root = workspace / "software" / "saxpy"
    out_mirror = dest / "source-downloads"
    assert f"spack -e {env_root} mirror create -d {out_mirror} --all" in fake_spack
    # Files from an earlier dump are not regenerated
    assert (dest / "url-info.txt").read_text() == "kept\n"
    assert f"spack -e {env_root} logs saxpy" not in fake_spack
    assert (dest / "saxpy-extracted-commands.txt").exists()


def test_show_build_requires_spack_environment(tmp_path):
    with pytest.raises(Exception, match="Could not find spack.yaml"):
        show_build.command(_args(tmp_path, tmp_path / "dump"))
