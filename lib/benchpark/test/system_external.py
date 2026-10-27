# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import json
import re
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

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
    package_dir = Path(system_external.__file__).resolve().parent
    assert command[4] == str(package_dir / "spack_helper.py")


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
    package_dir = Path(system_external.__file__).resolve().parent
    assert environment["BENCHPARK_SPACK_HELPER"] == str(package_dir / "spack_helper.py")
    assert captured["command"][:3] == [
        "/bin/bash",
        "-l",
        str(package_dir / "module_validator.sh"),
    ]
    assert result["spack_detection"] == expected_detection


def external(version, variants="", prefix="/usr/tce", **kwargs):
    spec = f"python@={version}{variants}"
    return system_external._External(
        package="python",
        raw_spec=spec,
        spec=spec,
        version=version,
        raw_prefix=prefix,
        prefix=prefix,
        modules=(),
        **kwargs,
    )


def detection(*externals):
    return {
        "outcome": "success",
        "finders": [
            {
                "records": [
                    {
                        "status": "ok",
                        "package": item.package,
                        "raw_spec": item.raw_spec,
                        "spec": item.spec,
                        "version": item.version,
                        "prefix": item.prefix,
                        "satisfies": list(item.satisfies_specs),
                    }
                    for item in externals
                ]
            }
        ],
    }


@pytest.fixture
def canonical_specs(monkeypatch):
    """The detection fixtures already contain exact canonical version strings."""

    def canonicalize(declarations):
        return [
            replace(
                item,
                spec=item.raw_spec,
                version=re.search(r"@=([\d.]+)", item.raw_spec)[1],
            )
            for item in declarations
        ]

    monkeypatch.setattr(
        system_external, "_canonicalize_declared_externals", canonicalize
    )


@pytest.mark.parametrize("new_versions", [("3.13.2",), ("3.13.2", "3.14.0")])
def test_new_versions_do_not_replace_missing_versions(new_versions):
    old = external("3.9.12")
    found = [external(version, "+ssl") for version in new_versions]
    result = system_external._reconcile_package("python", [old], found)

    assert result.declarations[0].state == "NOT_FOUND"
    assert result.declarations[0].matched_candidate is None
    assert [item.classification for item in result.candidates] == [
        "ADDITIONAL_VERSION"
    ] * len(found)
    proposals = system_external._logical_proposals(result)
    assert [
        item.candidate for item in proposals if item.action == "ADDITIONAL_VERSION"
    ] == found
    assert all(item.action != "REPLACEMENT" for item in proposals)


@pytest.mark.parametrize("satisfies", [False, True])
def test_existing_version_spec_updates_independently(satisfies):
    old = external("3.9.12")
    found = external("3.9.12", "+ssl", satisfies_specs=(old.spec,) if satisfies else ())
    missing = external("3.6.8")
    added = external("3.13.2", "+ssl")
    validations = [
        system_external._DeclarationResult(old, "VALID" if satisfies else "NOT_FOUND"),
        system_external._DeclarationResult(missing, "NOT_FOUND"),
    ]
    result = system_external._reconcile_package(
        "python", [old, missing], [found, added], validations
    )

    assert [item.state for item in result.declarations] == ["REPLACEMENT", "NOT_FOUND"]
    assert result.declarations[0].matched_candidate == found
    assert result.candidates[1].classification == "ADDITIONAL_VERSION"


def test_spec_updates_match_versions_and_prefixes_before_cardinality():
    old = [external("3.9.12", "~ssl", prefix) for prefix in ("/usr", "/usr/tce")]
    found = [external("3.9.12", "+ssl", prefix) for prefix in ("/usr/tce", "/usr")]
    result = system_external._reconcile_package("python", old, found)

    assert all(item.state == "REPLACEMENT" for item in result.declarations)
    assert [item.matched_candidate.prefix for item in result.declarations] == [
        "/usr",
        "/usr/tce",
    ]


def test_existing_exact_spec_wins_over_other_same_version_specs():
    old = external("3.9.12", "+ssl")
    result = system_external._reconcile_package(
        "python", [old], [external("3.9.12", "~ssl"), old]
    )
    assert result.declarations[0].state == "VALID"
    assert result.declarations[0].matched_candidate == old
    assert result.candidates[0].classification == "ADDITIONAL_SPEC"


def test_ambiguous_same_version_update_does_not_block_new_version():
    old = external("3.9.12")
    result = system_external._reconcile_package(
        "python",
        [old],
        [external("3.9.12", "+ssl"), external("3.9.12", "~ssl"), external("3.13.2")],
    )
    assert result.declarations[0].reason == "AMBIGUOUS_MATCH"
    assert result.candidates[-1].classification == "ADDITIONAL_VERSION"
    assert [item.action for item in system_external._logical_proposals(result)] == [
        "ADDITIONAL_VERSION"
    ]


def test_same_version_can_update_a_changed_prefix():
    old = external("3.9.12", prefix="/old")
    found = external("3.9.12", "+ssl", prefix="/new")
    result = system_external._reconcile_package("python", [old], [found])
    assert result.declarations[0].state == "REPLACEMENT"
    assert result.declarations[0].matched_candidate == found


@pytest.mark.parametrize("broad_outcome", ["success", "failed"])
def test_targeted_discoveries_become_candidates(
    monkeypatch, canonical_specs, broad_outcome
):
    old = external("3.9.12")
    known = external("2.7.18")
    added = external("3.13.2", "+ssl")
    system = SimpleNamespace(
        compute_packages_section=lambda: {
            "packages": {
                "python": {
                    "externals": [
                        {"spec": item.spec, "prefix": item.prefix}
                        for item in (old, known)
                    ]
                }
            }
        },
        compute_compilers_section=lambda: {},
    )
    calls = []

    def batch(requests):
        calls.append(requests)
        if requests[0]["initial_guess"] is None:
            return {"python": dict(detection(known), outcome=broad_outcome)}
        return {"python": detection(known, added)}

    monkeypatch.setattr(system_external, "_run_spack_batch", batch)
    (result,) = system_external._reconcile_system_externals(system)

    assert len(calls) == 2
    assert calls[1][0]["initial_guess"] == ["/usr/tce"]
    assert [item.state for item in result.declarations] == ["NOT_FOUND", "VALID"]
    assert len(result.candidates) == 2
    discovered = next(
        item for item in result.candidates if item.external.version == "3.13.2"
    )
    assert discovered.classification == "ADDITIONAL_VERSION"
    assert discovered.external.observed_by == ("targeted_prefix_validation",)


def test_shared_source_addition_and_update_apply_together(monkeypatch, canonical_specs):
    old = external("3.9.12", "~ssl")
    found = external("3.9.12", "+ssl")
    added = external("3.13.2", "+ssl")
    missing = external("3.6.8")
    source = (
        'packages = {"python": {"externals": [\n'
        + "".join(
            f'    {{"spec": "{item.spec}", "prefix": "{item.prefix}"}},\n'
            for item in (missing, old)
        )
        + "]}}\n"
    )
    result = system_external._reconcile_package(
        "python", [missing, old], [found, added]
    )
    result = replace(result, validator_outcome="SUCCESS")
    monkeypatch.setattr(
        system_external, "_cluster_scope", lambda *args: (("magma",), None)
    )
    (proposed,) = system_external._with_source_proposals(None, (result,), source)

    assert all(item.source_mutable for item in proposed.proposals)
    assert all(item.also_changes == ("magma",) for item in proposed.proposals)
    rewritten = source
    for proposal in proposed.proposals:
        rewritten, reason = system_external._proposal_source_edit(rewritten, proposal)
        assert reason is None
    namespace = {}
    exec(rewritten, namespace)
    entries = namespace["packages"]["python"]["externals"]
    assert {item["spec"] for item in entries} == {missing.spec, found.spec, added.spec}
    assert len(entries) == 3
    assert "external-status=" not in rewritten
    declarations = system_external._canonicalize_declared_externals(
        system_external._extract_declared_externals(namespace["packages"])
    )
    assert system_external._external_counter(
        declarations
    ) == system_external._expected_external_delta((result,), proposed.proposals)
    (reconciled,) = system_external._reconcile_frozen_evidence((result,), declarations)
    assert {item.external.version: item.state for item in reconciled.declarations} == {
        "3.6.8": "NOT_FOUND",
        "3.9.12": "VALID",
        "3.13.2": "VALID",
    }
    (repeated,) = system_external._with_source_proposals(None, (reconciled,), rewritten)
    assert not any(item.source_mutable for item in repeated.proposals)


def test_apply_shared_system_transaction(monkeypatch, tmp_path, canonical_specs):
    repo = system_external.benchpark.repo
    spec_module = system_external.benchpark.spec
    (tmp_path / "repo.yaml").write_text(
        "repo:\n  namespace: externaltest\n  subdirectory: ''\n"
    )
    directory = tmp_path / "example"
    directory.mkdir()
    path = directory / "system.py"
    source = """from benchpark.directives import variant
from benchpark.system import System

class Example(System):
    variant("cluster", values=("dane", "magma"), default="dane", description="Cluster")

    def compute_packages_section(self):
        return {"packages": {"python": {"externals": [
            {"spec": "python@=2.7.18", "prefix": "/usr/tce"},
            {"spec": "python@=3.9.12", "prefix": "/usr/tce"},
        ]}}}

    def compute_compilers_section(self):
        return {}
"""
    path.write_text(source)
    known = external("2.7.18")
    added = external("3.13.2", "+ssl")
    monkeypatch.setattr(
        system_external,
        "_run_spack_batch",
        lambda requests: {
            "python": (
                detection(known, added) if requests[0]["initial_guess"] else detection()
            )
        },
    )
    with repo.override_ramble_hardcoded_globals():
        with repo.use_repositories(
            str(tmp_path), object_type=repo.ObjectTypes.systems
        ) as repositories:
            monkeypatch.setattr(spec_module, "sys_repo", repositories)
            spec = spec_module.SystemSpec(
                "externaltest.example cluster=dane"
            ).concretize()
            results = system_external._reconcile_system_externals(spec.system)
            results = system_external._with_source_proposals(spec, results, source)
            assert all(proposal.source_mutable for proposal in results[0].proposals)
            assert all(
                proposal.also_changes == ("magma",) for proposal in results[0].proposals
            )
            reconciled, applied = system_external._apply_source_proposals(
                spec, results, path, source.encode(), source
            )
            assert applied
            rewritten = path.read_text()
            assert '"python@=3.9.12"' in rewritten
            assert '"python@=3.13.2+ssl"' in rewritten
            assert "external-status=" not in rewritten
            repeated = system_external._with_source_proposals(
                spec, reconciled, rewritten
            )
            assert not any(
                proposal.source_mutable for proposal in repeated[0].proposals
            )


def test_unconfirmed_version_does_not_change_source(tmp_path, capsys):
    old = external("3.9.12")
    source = f'packages = {{"python": {{"externals": [{{"spec": "{old.spec}", "prefix": "{old.prefix}"}}]}}}}\n'
    path = tmp_path / "system.py"
    path.write_text(source)
    result = system_external._reconcile_package("python", [old], [])
    results = system_external._with_source_proposals(None, (result,), source)

    assert results[0].declarations[0].state == "NOT_FOUND"
    assert results[0].proposals == ()
    _, applied = system_external._apply_source_proposals(
        None, results, path, source.encode(), source
    )
    assert not applied
    assert path.read_bytes() == source.encode()
    with system_external.color.color_when(False):
        system_external._report_reconciliation("example", results)
    assert "NOT_FOUND:" in capsys.readouterr().out


def test_new_version_can_be_added_with_unresolved_declarations(monkeypatch):
    old = external("3.9.12")
    added = external("3.13.2")
    result = system_external._reconcile_package(
        "python",
        [old],
        [added],
        [system_external._DeclarationResult(old, "REVIEW_REQUIRED")],
    )
    source = f'packages = {{"python": {{"externals": [{{"spec": "{old.spec}", "prefix": "{old.prefix}"}}]}}}}\n'
    monkeypatch.setattr(system_external, "_cluster_scope", lambda *args: ((), None))
    (proposed,) = system_external._with_source_proposals(None, (result,), source)
    assert len(proposed.proposals) == 1
    assert proposed.proposals[0].source_mutable


@pytest.mark.parametrize("colored", [True, False, None])
def test_report_color_preserves_specs_and_plain_output(capsys, colored):
    old = external("3.9.12")
    added = external("3.13.2", "+ssl")
    result = system_external._reconcile_package("python", [old], [added])
    result = replace(
        result, proposals=tuple(system_external._logical_proposals(result))
    )
    with system_external.color.color_when(colored):
        system_external._report_reconciliation("example", (result,))
    output = capsys.readouterr().out
    assert ("\x1b[" in output) == (colored is True)
    assert old.spec in output
    assert added.spec in output
    plain = re.sub(r"\x1b\[[0-9;]*m", "", output)
    assert "NOT_FOUND:" in plain
    assert "ADDITIONAL_VERSION:" in plain
    assert "proposal ADDITIONAL_VERSION [report-only]" in plain
    assert "@*" not in plain
