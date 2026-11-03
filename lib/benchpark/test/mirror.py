# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import subprocess

import pytest

import benchpark.cmd.mirror as mirror
import benchpark.runtime
from benchpark.paths import paths


def _git_repo(path, files, untracked=()):
    """Create a git repository whose index tracks ``files``."""
    for relpath, text in files.items():
        (path / relpath).parent.mkdir(parents=True, exist_ok=True)
        (path / relpath).write_text(text)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    for relpath in untracked:
        (path / relpath).parent.mkdir(parents=True, exist_ok=True)
        (path / relpath).write_text("untracked\n")


@pytest.fixture
def benchpark_workspace(tmp_path):
    """A Benchpark workspace laid out the way `benchpark setup` creates it."""
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "setup.sh").write_text("# setup\n")
    _git_repo(
        root / "spack",
        {
            "bin/spack": "#!/bin/sh\n",
            "etc/spack/config.yaml": "config: {}\n",
            "etc/spack/README": "kept\n",
            "lib/spack/docs/_static/spack-logo-text.svg": "<svg/>\n",
        },
        untracked=["scratch/notes.txt"],
    )
    _git_repo(
        root / "ramble",
        {"bin/ramble": "#!/bin/sh\n", "etc/ramble/config.yaml": "config: {}\n"},
    )
    _git_repo(
        root / "spack-packages", {"repos/spack_repo/builtin/repo.yaml": "repo: {}\n"}
    )
    ramble_workspace = root / "dane" / "saxpy" / "workspace"
    for relpath in [
        "configs/ramble.yaml",
        "software/saxpy/spack.yaml",
        "logs/setup.log",
        "experiments/saxpy/execute_experiment",
    ]:
        (ramble_workspace / relpath).parent.mkdir(parents=True, exist_ok=True)
        (ramble_workspace / relpath).write_text(relpath + "\n")
    return root, ramble_workspace


@pytest.fixture
def recorded_commands(monkeypatch):
    """Stand in for the pip/spack/ramble commands mirror_create shells out to.

    git and rm still run for real so the copies can be checked."""
    calls = []
    real_run_command = benchpark.runtime.run_command

    def fake_run_command(command, *args, **kwargs):
        calls.append(command)
        if command.startswith(("git ", "rm ")):
            return real_run_command(command, *args, **kwargs)
        if "env-collect-branch-tips.py" in command:
            return '{"saxpy": "0123abc"}', ""
        # pip download, spack bootstrap mirror and ramble workspace mirror
        # all create their destination directory
        destination = command.split()[-1].replace("file://", "")
        os.makedirs(destination, exist_ok=True)
        return "", ""

    monkeypatch.setattr(mirror, "run_command", fake_run_command)
    return calls


def _args(workspace, destdir, dry_run=False):
    return argparse.Namespace(
        system_subcommand="create",
        dry_run=dry_run,
        workspace=str(workspace),
        destdir=str(destdir),
    )


def test_mirror_create_copies_workspace_for_offline_use(
    benchpark_workspace, recorded_commands, tmp_path
):
    root, ramble_workspace = benchpark_workspace
    dest = tmp_path / "mirror"

    mirror.command(_args(ramble_workspace, dest))

    assert (dest / ".benchpark-mirror-dir").exists()

    # The Ramble workspace is copied without built software or logs
    copied = dest / "dane" / "saxpy" / "workspace"
    assert (copied / "configs" / "ramble.yaml").exists()
    assert (copied / "experiments" / "saxpy" / "execute_experiment").exists()
    assert not (copied / "software").exists()
    assert not (copied / "logs").exists()

    # Only top-level entries tracked by git (plus .git) are copied, and the
    # copied Spack/Ramble configs are removed
    assert (dest / "spack" / "bin" / "spack").exists()
    assert (dest / "spack" / ".git").is_dir()
    assert not (dest / "spack" / "scratch").exists()
    assert not (dest / "spack" / "etc" / "spack" / "config.yaml").exists()
    assert (dest / "spack" / "etc" / "spack" / "README").exists()
    assert not (dest / "ramble" / "etc" / "ramble" / "config.yaml").exists()
    assert (dest / "spack-packages" / "repos" / "spack_repo" / "builtin").is_dir()

    # SVGs known to break the copy are deleted from the source Spack
    svg = root / "spack" / "lib" / "spack" / "docs" / "_static" / "spack-logo-text.svg"
    assert not svg.exists()

    assert (dest / "git-commit-info.json").read_text() == '{"saxpy": "0123abc"}'
    assert (dest / "redirect-git-urls.py").exists()
    assert (dest / "modifiers").is_dir()
    assert (dest / "repos" / "ramble_applications").is_dir()
    assert "spack/share/spack/setup-env.sh" in (dest / "setup.sh").read_text()
    first_time = (dest / "first-time.sh").read_text()
    assert "redirect-git-urls.py $this_script_dir/dane git-commit-info.json" in (
        first_time
    )

    env_dir = ramble_workspace / "software" / "saxpy"
    req_file = paths.benchpark_root / "requirements.txt"
    assert f"pip download -r {req_file} -d {dest / 'pip-cache'}" in recorded_commands
    assert any(c.startswith(f"spack -e {env_dir} python ") for c in recorded_commands)
    assert f"spack bootstrap mirror {dest / 'spack-bootstrap-mirror'}" in (
        recorded_commands
    )
    assert (
        f"ramble --workspace-dir {ramble_workspace} workspace mirror "
        f"-d file://{dest / 'ramble-workspace-mirror'}"
    ) in recorded_commands


def test_mirror_create_reuses_existing_mirror(
    benchpark_workspace, recorded_commands, tmp_path
):
    _, ramble_workspace = benchpark_workspace
    dest = tmp_path / "mirror"
    mirror.command(_args(ramble_workspace, dest))
    (dest / "setup.sh").write_text("edited\n")
    first_pass = len(recorded_commands)

    mirror.command(_args(ramble_workspace, dest))

    # Existing pieces are left alone; nothing is downloaded or cloned again
    assert (dest / "setup.sh").read_text() == "edited\n"
    second_pass = recorded_commands[first_pass:]
    assert not any(
        c.startswith(("pip download", "git ls-files", "spack bootstrap", "ramble "))
        for c in second_pass
    )


def test_mirror_create_refuses_foreign_destination(
    benchpark_workspace, recorded_commands, tmp_path
):
    _, ramble_workspace = benchpark_workspace

    not_a_mirror = tmp_path / "existing"
    not_a_mirror.mkdir()
    with pytest.raises(RuntimeError, match="was not created by `benchpark mirror`"):
        mirror.command(_args(ramble_workspace, not_a_mirror))

    a_file = tmp_path / "file"
    a_file.write_text("")
    with pytest.raises(RuntimeError, match="is not a directory"):
        mirror.command(_args(ramble_workspace, a_file))

    assert recorded_commands == []


def test_mirror_create_requires_benchpark_workspace(tmp_path, recorded_commands):
    lone_ramble_workspace = tmp_path / "just" / "a" / "workspace"
    lone_ramble_workspace.mkdir(parents=True)

    with pytest.raises(RuntimeError, match="Cannot locate Benchpark workspace"):
        mirror.command(_args(lone_ramble_workspace, tmp_path / "mirror"))


def test_copytree_tracked_requires_git_repo(tmp_path):
    (tmp_path / "src").mkdir()
    with pytest.raises(RuntimeError, match="Not a git repo"):
        mirror.copytree_tracked(str(tmp_path / "src"), str(tmp_path / "dest"))


def test_find_one_matches_by_regex(tmp_path):
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "spack.yaml").write_text("")

    assert mirror.find_one(str(tmp_path), "spack.yaml") == str(
        tmp_path / "a" / "b" / "spack.yaml"
    )
    assert mirror.find_one(str(tmp_path), "missing.yaml") is None


def test_dry_run_command_prints_instead_of_running(capsys):
    mirror._dry_run_command("spack install", "extra", key="value")

    out = capsys.readouterr().out
    assert "spack install" in out
    assert "('extra',)" in out
    assert "{'key': 'value'}" in out
