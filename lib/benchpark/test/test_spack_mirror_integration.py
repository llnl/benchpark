# Copyright 2026 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

SPACK_EXE = shutil.which("spack")

requires_spack = pytest.mark.skipif(
    SPACK_EXE is None, reason="spack executable not found on PATH"
)

PACKAGE_PY_TEMPLATE = '''\
# Copyright 2026 Lawrence Livermore National Security, LLC
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Mypackage(Package):
    """Test package with a branch-based git version."""

    homepage = "https://example.com"
    git = "{git_url}"

    version("develop", branch="develop", git="{git_url}")

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
'''


PACKAGE_PY_NON_BRANCH_TEMPLATE = '''\
# Copyright 2026 Lawrence Livermore National Security, LLC
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Otherpackage(Package):
    """Test package with a non-branch version."""

    homepage = "https://example.com"

    version("1.0")

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
'''


REPO_YAML = """\
repo:
  namespace: myrepo
  api: v2.0
"""


def _run(cmd, env=None, cwd=None, timeout=120):
    """Run a command, capturing output, and raise a clear error on failure.

    ``env`` entries are merged into the current environment so that
    Spack isolation variables (e.g. ``SPACK_USER_CONFIG_PATH``) propagate
    to every subprocess without clobbering ``PATH`` or other needed vars.
    """
    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=merged_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    return result


def _make_git_repo(path):
    """Create a local git repo with a `develop` branch and two commits."""
    path.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", "-q"], cwd=path)
    (path / "README.md").write_text("initial\n")
    _run(["git", "add", "README.md"], cwd=path)
    _run(["git", "commit", "-q", "-m", "initial"], cwd=path)
    _run(["git", "checkout", "-q", "-b", "develop"], cwd=path)
    (path / "README.md").write_text("develop\n")
    _run(["git", "add", "README.md"], cwd=path)
    _run(["git", "commit", "-q", "-m", "develop"], cwd=path)
    commit = subprocess.run(
        ["git", "rev-parse", "develop"],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return path, commit


def _make_spack_package_repo(base, git_url, env=None):
    """Create an API v2.0 Spack package repository with mypackage@develop.

    Registers the repository with Spack and discovers system compilers so
    concretization does not fail on systems without auto-detected compilers.
    All Spack subprocesses use the isolated environment ``env``.
    """
    repo_root = base / "spack_repo" / "myrepo"
    (repo_root / "packages" / "mypackage").mkdir(parents=True)
    (repo_root / "repo.yaml").write_text(REPO_YAML)
    (repo_root / "packages" / "mypackage" / "package.py").write_text(
        PACKAGE_PY_TEMPLATE.format(git_url=git_url)
    )
    _run([SPACK_EXE, "repo", "add", str(repo_root)], env=env)
    _run([SPACK_EXE, "compiler", "find"], env=env)
    return repo_root


def _make_spack_environment(base, specs=None, env=None):
    """Create a minimal Spack environment concretizing the given specs.

    All Spack subprocesses use the isolated environment ``env``.
    """
    if specs is None:
        specs = ["mypackage@develop"]
    env_dir = base / "env"
    env_dir.mkdir(parents=True)
    specs_yaml = "\n".join(f"    - {s}" for s in specs)
    (env_dir / "spack.yaml").write_text(
        f"""\
spack:
  specs:
{specs_yaml}
  concretizer:
    unify: true
"""
    )
    _run([SPACK_EXE, "-e", str(env_dir), "concretize"], env=env)
    return env_dir


def _make_workspace(base):
    """Create a BenchPark-style workspace with auxiliary_software_files/packages.yaml."""
    ws = base / "workspace"
    aux = ws / "auxiliary_software_files"
    aux.mkdir(parents=True)
    (aux / "packages.yaml").write_text(
        """\
packages:
  mypackage:
    buildable: False
"""
    )
    return ws


def _validate_packages_config(spack_exe, aux_path, env=None, timeout=60):
    """Load packages.yaml through Spack's config system and return the parsed dict.

    Runs under the isolated Spack environment ``env`` so configuration
    cannot leak into the user's global Spack configuration.
    """
    validate_code = (
        "import json, spack.config\n"
        f'ds = spack.config.DirectoryConfigScope("auxpath", {str(aux_path)!r})\n'
        "cfg = spack.config.create_from(ds)\n"
        'pkgs = cfg.get("packages", scope="auxpath")\n'
        "print(json.dumps(pkgs))\n"
    )
    result = _run(
        [spack_exe, "python", "-c", validate_code],
        env=env,
        timeout=timeout,
    )
    return json.loads(result.stdout)


@pytest.fixture
def spack_config_dir(tmp_path):
    """Isolated Spack user configuration directory.

    Each test function gets its own directory, so Spack configuration
    changes (e.g. ``spack repo add``) cannot leak between tests or into
    the user's global Spack configuration.
    """
    config_dir = tmp_path / "spack-user-config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return str(config_dir)


@pytest.fixture
def spack_env_vars(spack_config_dir):
    """Environment variables for isolated Spack configuration.

    ``SPACK_USER_CONFIG_PATH`` redirects all Spack config reads/writes to
    the temporary directory. Other environment variables (e.g. ``PATH``)
    are preserved via the merge in ``_run``.
    """
    return {"SPACK_USER_CONFIG_PATH": spack_config_dir}


@pytest.fixture
def git_repo(tmp_path):
    """A local git repository with a `develop` branch."""
    return _make_git_repo(tmp_path / "git-repo")


@pytest.fixture
def spack_package_repo(tmp_path, git_repo, spack_env_vars):
    """A Spack package repository registered with the cloned Spack.

    Uses isolated Spack configuration so repository registration cannot
    collide with other tests sharing the same namespace.
    """
    repo_path, _ = git_repo
    git_url = f"file://{repo_path}"
    pkg_repo = _make_spack_package_repo(
        tmp_path / "spack-repo", git_url, env=spack_env_vars
    )
    return pkg_repo, git_url


@pytest.fixture
def spack_env(tmp_path, spack_package_repo, spack_env_vars):
    """A concretized Spack environment with mypackage@develop.

    Uses the same isolated Spack configuration as the package repository
    fixture so concretization sees the registered packages.
    """
    return _make_spack_environment(tmp_path / "env", env=spack_env_vars)


@pytest.fixture
def benchpark_scripts():
    """Paths to the two mirror scripts under test."""
    benchpark_root = Path(__file__).resolve().parents[3]
    return {
        "collect": benchpark_root / "lib" / "scripts" / "env-collect-branch-tips.py",
        "redirect": benchpark_root / "lib" / "scripts" / "redirect-git-urls.py",
    }


@requires_spack
def test_env_collect_branch_tips_collects_branch_commit(
    spack_env, git_repo, benchpark_scripts, spack_env_vars
):
    """Test A: env-collect-branch-tips.py emits @version commit=<sha> for branch-based packages."""
    _, develop_commit = git_repo
    collect = benchpark_scripts["collect"]

    result = _run(
        [SPACK_EXE, "-e", str(spack_env), "python", str(collect)],
        env=spack_env_vars,
        timeout=120,
    )

    requirements = json.loads(result.stdout)
    assert "mypackage" in requirements, (
        f"Expected mypackage in output, got: {result.stdout}"
    )
    expected = f"@develop commit={develop_commit}"
    assert requirements["mypackage"] == expected, (
        f"Expected {expected!r}, got {requirements['mypackage']!r}"
    )


@requires_spack
def test_env_collect_branch_tips_excludes_non_branch_package(
    tmp_path, git_repo, benchpark_scripts, spack_env_vars
):
    """Test B: packages without branch-based git versions are excluded."""
    repo_path, _ = git_repo
    git_url = f"file://{repo_path}"

    pkg_repo = _make_spack_package_repo(
        tmp_path / "spack-repo", git_url, env=spack_env_vars
    )

    # Add a second, non-branch package to the same repo
    other_dir = pkg_repo / "packages" / "otherpackage"
    other_dir.mkdir(parents=True)
    (other_dir / "package.py").write_text(PACKAGE_PY_NON_BRANCH_TEMPLATE)

    env_dir = _make_spack_environment(
        tmp_path / "env",
        specs=["mypackage@develop", "otherpackage@1.0"],
        env=spack_env_vars,
    )

    collect = benchpark_scripts["collect"]
    result = _run(
        [SPACK_EXE, "-e", str(env_dir), "python", str(collect)],
        env=spack_env_vars,
        timeout=120,
    )

    requirements = json.loads(result.stdout)
    assert "mypackage" in requirements, (
        f"Expected mypackage in output, got: {result.stdout}"
    )
    assert "otherpackage" not in requirements, (
        f"otherpackage should be excluded (non-branch), got: {result.stdout}"
    )


@requires_spack
def test_redirect_git_urls_adds_require_constraint(
    tmp_path, git_repo, benchpark_scripts, spack_env_vars
):
    """Test C: redirect-git-urls.py appends require constraint to packages config."""
    _, develop_commit = git_repo
    redirect = benchpark_scripts["redirect"]

    workspace = _make_workspace(tmp_path / "workspace")

    # Copy redirect script next to commit-info file (script resolves paths relative to itself)
    commit_info = {
        "mypackage": f"@develop commit={develop_commit}",
    }
    script_dst = tmp_path / "redirect-git-urls.py"
    shutil.copyfile(redirect, script_dst)
    (tmp_path / "git-commit-info.json").write_text(json.dumps(commit_info, indent=2))

    _run(
        [SPACK_EXE, "python", str(script_dst), str(workspace), "git-commit-info.json"],
        env=spack_env_vars,
        cwd=tmp_path,
        timeout=60,
    )

    # Validate through Spack's config system (not just YAML text)
    aux_path = workspace / "auxiliary_software_files"
    pkgs = _validate_packages_config(SPACK_EXE, aux_path, env=spack_env_vars)

    assert "mypackage" in pkgs, f"Expected mypackage in packages config, got: {pkgs}"
    assert "require" in pkgs["mypackage"], (
        f"Expected require in mypackage config, got: {pkgs['mypackage']}"
    )
    require_list = pkgs["mypackage"]["require"]
    assert isinstance(require_list, list), (
        f"Expected require to be a list, got: {type(require_list)}"
    )
    expected = f"@develop commit={develop_commit}"
    assert expected in require_list, (
        f"Expected {expected!r} in require list, got: {require_list}"
    )


@requires_spack
def test_redirect_git_urls_preserves_existing_require(
    tmp_path, git_repo, benchpark_scripts, spack_env_vars
):
    """Test D: existing require list is preserved and new constraint appended."""
    _, develop_commit = git_repo
    redirect = benchpark_scripts["redirect"]

    workspace = _make_workspace(tmp_path / "workspace")
    aux_path = workspace / "auxiliary_software_files"

    # Pre-existing require as a list (as generated by system.py)
    (aux_path / "packages.yaml").write_text(
        """\
packages:
  mypackage:
    buildable: False
    require:
      - "@1.0 commit=oldhash"
"""
    )

    commit_info = {
        "mypackage": f"@develop commit={develop_commit}",
    }
    script_dst = tmp_path / "redirect-git-urls.py"
    shutil.copyfile(redirect, script_dst)
    (tmp_path / "git-commit-info.json").write_text(json.dumps(commit_info, indent=2))

    _run(
        [SPACK_EXE, "python", str(script_dst), str(workspace), "git-commit-info.json"],
        env=spack_env_vars,
        cwd=tmp_path,
        timeout=60,
    )

    pkgs = _validate_packages_config(SPACK_EXE, aux_path, env=spack_env_vars)

    require_list = pkgs["mypackage"]["require"]
    assert "@1.0 commit=oldhash" in require_list, (
        f"Existing require should be preserved, got: {require_list}"
    )
    expected = f"@develop commit={develop_commit}"
    assert expected in require_list, (
        f"New require should be appended, got: {require_list}"
    )
    assert len(require_list) == 2, (
        f"Expected 2 require entries, got {len(require_list)}: {require_list}"
    )
