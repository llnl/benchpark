# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
from unittest.mock import Mock

import pytest

import benchpark.runtime as runtime


@pytest.fixture
def ramble_requirements(tmp_path, monkeypatch):
    resources = runtime.RuntimeResources(tmp_path / "bootstrap with spaces")
    resources.ramble_location.mkdir(parents=True)
    requirements = resources.ramble_location / "requirements.txt"
    requirements.write_text("example>=2\n")
    installed = {}

    def version(name):
        if name not in installed:
            raise runtime.importlib.metadata.PackageNotFoundError(name)
        return installed[name]

    monkeypatch.setattr(runtime.importlib.metadata, "version", version)
    install = Mock()
    monkeypatch.setattr(runtime.subprocess, "check_call", install)
    return resources, requirements, installed, install


@pytest.mark.parametrize(
    "contents, installed_version, needs_install",
    [
        ("example>=2\n", None, True),
        ("example>=2\n", "1.9", True),
        ("example<2\n", "2.1", True),
        ("example>=2\n", "2.1", False),
        ("# Comment\n\nexample>=2\t# Inline comment\n", "2.1", False),
        ('example; python_version < "3.8"\n', None, False),
        ('example; python_version >= "3.8"\n', None, True),
        ("-r other.txt\n", "2.1", True),
        ("example[extra]\n", "2.1", True),
        ("example @ https://example.org/example.whl\n", "2.1", True),
    ],
)
def test_ramble_requirements(
    ramble_requirements, contents, installed_version, needs_install
):
    resources, requirements, installed, install = ramble_requirements
    requirements.write_text(contents)
    if installed_version is not None:
        installed["example"] = installed_version

    resources._ensure_ramble_requirements()

    if needs_install:
        install.assert_called_once_with(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements)]
        )
    else:
        install.assert_not_called()


def test_ramble_requirements_recheck_environment_and_checkout(ramble_requirements):
    resources, requirements, installed, install = ramble_requirements
    installed["example"] = "2.1"
    resources._ensure_ramble_requirements()
    install.assert_not_called()

    # A new requirement at a different Ramble commit must trigger installation.
    requirements.write_text("example>=3\n")
    resources._ensure_ramble_requirements()
    assert install.call_count == 1

    # Once satisfied, repeated use of the same checkout does not invoke pip.
    installed["example"] = "3.0"
    resources._ensure_ramble_requirements()
    assert install.call_count == 1

    # Switching environments or removing a package must trigger installation again.
    installed.clear()
    resources._ensure_ramble_requirements()
    assert install.call_count == 2


def test_ramble_requirements_retry_failed_install(ramble_requirements):
    resources, _, _, install = ramble_requirements
    install.side_effect = [subprocess.CalledProcessError(1, "pip"), 0]
    with pytest.raises(subprocess.CalledProcessError):
        resources._ensure_ramble_requirements()
    resources._ensure_ramble_requirements()
    assert install.call_count == 2


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("fails", [False, True])
def test_bootstrap_installs_requirements_before_imports(
    tmp_path, monkeypatch, existing, fails
):
    resources = runtime.RuntimeResources(tmp_path)
    events = []
    if existing:
        resources.ramble_location.mkdir()
    monkeypatch.setattr(resources, "_install_ramble", lambda: events.append("clone"))
    monkeypatch.setattr(
        resources, "_check_and_update_bootstrap", lambda *args: events.append("update")
    )

    def ensure():
        events.append("requirements")
        if fails:
            raise subprocess.CalledProcessError(1, "pip")

    monkeypatch.setattr(resources, "_ensure_ramble_requirements", ensure)
    monkeypatch.setattr(resources, "_install_packages", lambda: None)
    monkeypatch.setattr(resources, "_install_spack", lambda: None)
    monkeypatch.setattr(
        resources, "_register_spack_utilities", lambda: events.append("import")
    )
    monkeypatch.setattr(sys, "path", sys.path[:])

    if fails:
        with pytest.raises(subprocess.CalledProcessError):
            resources.bootstrap()
    else:
        resources.bootstrap()
    assert events == ["update" if existing else "clone", "requirements"] + (
        [] if fails else ["import"]
    )


def test_workspace_ramble_installs_requirements(tmp_path, monkeypatch):
    resources = runtime.RuntimeResources(tmp_path)
    events = []

    def clone():
        resources.ramble_location.mkdir()
        events.append("clone")

    monkeypatch.setattr(resources, "_install_ramble", clone)
    monkeypatch.setattr(
        resources, "_ensure_ramble_requirements", lambda: events.append("requirements")
    )
    command, first_time = resources.ramble_first_time_setup()
    assert first_time
    assert events == ["clone", "requirements"]
    assert command.env["RAMBLE_PYTHON"] == sys.executable

    resources.ramble()
    assert events == ["clone", "requirements", "requirements"]
