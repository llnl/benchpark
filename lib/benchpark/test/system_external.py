# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
from types import SimpleNamespace

import benchpark.system_external as system_external


def test_reconciliation_findings_are_successful():
    package_results = [
        SimpleNamespace(validator_outcome="SUCCESS"),
        SimpleNamespace(validator_outcome="UNSUPPORTED_DETECTION"),
        SimpleNamespace(validator_outcome="REVIEW_REQUIRED"),
    ]

    assert system_external._reconciliation_exit_status(package_results) == 0


def test_validator_failure_is_an_operational_failure():
    package_results = [SimpleNamespace(validator_outcome="VALIDATOR_FAILED")]

    assert system_external._reconciliation_exit_status(package_results) == 1


def test_spack_command_uses_pinned_package_repository(monkeypatch, tmp_path):
    monkeypatch.setattr(system_external.paths, "benchpark_home", tmp_path)

    command = system_external._spack_command()

    repository = tmp_path / "spack-packages/repos/spack_repo/builtin"
    assert command[:4] == [
        str(tmp_path / "spack/bin/spack"),
        "-c",
        f"repos:builtin:{repository}",
        "python",
    ]


def test_spack_environment_uses_bootstrap_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(system_external.paths, "benchpark_home", tmp_path)
    monkeypatch.setenv("SPACK_DISABLE_LOCAL_CONFIG", "0")
    monkeypatch.setenv("SPACK_USER_CACHE_PATH", "/unrelated/cache")

    environment = system_external._spack_environment()

    assert environment["SPACK_DISABLE_LOCAL_CONFIG"] == "1"
    assert environment["SPACK_USER_CACHE_PATH"] == str(tmp_path / "spack-user-cache")


def test_hybrid_module_validation_propagates_spack_settings(monkeypatch, tmp_path):
    monkeypatch.setattr(system_external.paths, "benchpark_home", tmp_path)
    captured = {}
    expected_detection = {"outcome": "success", "finders": []}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["environment"] = kwargs["env"]
        detection = {
            "status": "ok",
            "detection": expected_detection,
        }
        module_result = {
            "outcome": "valid",
            "failed_module": None,
            "detail": None,
            "loaded_modules": ["rocm/6.4.3"],
            "spack_status": "0",
        }
        stdout = "\n".join(
            [
                system_external._SPACK_RESULT_PREFIX + json.dumps(detection),
                system_external._MODULE_RESULT_PREFIX + json.dumps(module_result),
            ]
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(system_external.subprocess, "run", fake_run)

    result = system_external._validate_module_sequence(
        ["rocm/6.4.3"], hybrid_request={"action": "detect"}
    )

    repository = tmp_path / "spack-packages/repos/spack_repo/builtin"
    environment = captured["environment"]
    assert environment["BENCHPARK_SPACK_REPOSITORY_CONFIG"] == (
        f"repos:builtin:{repository}"
    )
    assert environment["SPACK_USER_CACHE_PATH"] == str(tmp_path / "spack-user-cache")
    assert result["spack_detection"] == expected_detection
