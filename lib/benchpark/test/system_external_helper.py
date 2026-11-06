# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for how `benchpark system external` talks to Spack and Lmod.

The first group runs the real spack_helper.py under `spack python`; the rest
drive the parsing and validation logic with canned helper output."""

import argparse
import json
import subprocess
from dataclasses import replace

import pytest

import benchpark.spec
import benchpark.system_external as system_external
from benchpark.system_external import (
    _CandidateResult,
    _DeclarationResult,
    _External,
    _PackageResult,
    _Proposal,
    _SpackHelperError,
)

SPACK_PREFIX = system_external._SPACK_RESULT_PREFIX
MODULE_PREFIX = system_external._MODULE_RESULT_PREFIX


# ---------------------------------------------------------------------------
# The real helper, run under `spack python`
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def fake_cmake(tmp_path_factory):
    """A prefix whose bin/cmake reports a version the way CMake does."""
    prefix = tmp_path_factory.mktemp("cmake-prefix")
    (prefix / "bin").mkdir()
    exe = prefix / "bin" / "cmake"
    exe.write_text('#!/bin/sh\necho "cmake version 3.27.0"\n')
    exe.chmod(0o755)
    return prefix


def test_spack_helper_canonicalizes_specs():
    response = system_external._run_spack_helper(
        {
            "action": "canonicalize",
            "specs": [
                {"id": 0, "spec": "cmake@3.27.0"},
                {"id": 1, "spec": "zlib@=1.3 +optimize"},
                {"id": 2, "spec": "@@not a spec"},
            ],
        }
    )

    records = {record["id"]: record for record in response["records"]}
    assert records[0]["status"] == "ok"
    assert (records[0]["package"], records[0]["spec"], records[0]["version"]) == (
        "cmake",
        "cmake@=3.27.0",
        "3.27.0",
    )
    assert records[1]["spec"] == "zlib@=1.3+optimize"
    assert records[2]["status"] == "invalid"
    assert "SpecTokenizationError" in records[2]["detail"]


def test_spack_helper_batch_detection(fake_cmake):
    results = system_external._run_spack_batch(
        [
            {
                "id": "cmake",
                "package": "cmake",
                "initial_guess": [str(fake_cmake / "bin")],
                "declared_specs": ["cmake@3.27.0", "cmake@3.28.0"],
            },
            {"id": "virtual", "package": "mpi"},
            {"id": "unknown", "package": "not-a-spack-package"},
            {"id": "bad-guess", "package": "cmake", "initial_guess": "not-a-list"},
            {"id": "bad-specs", "package": "cmake", "declared_specs": [""]},
            {"id": "no-package", "package": ""},
        ]
    )

    finders = {finder["name"]: finder for finder in results["cmake"]["finders"]}
    assert results["cmake"]["outcome"] == "success"
    assert finders["libraries"]["status"] == "not_applicable"
    (record,) = finders["executables"]["records"]
    assert record["status"] == "ok"
    assert (record["spec"], record["prefix"]) == ("cmake@=3.27.0", str(fake_cmake))
    assert record["satisfies"] == ["cmake@3.27.0"]

    assert results["virtual"]["outcome"] == "no_applicable_validator"
    assert "UnknownPackageError" in results["unknown"]["detail"]
    assert results["bad-guess"]["detail"] == "initial_guess must be a list or null"
    assert results["bad-specs"]["detail"] == (
        "declared_specs must be a list of non-empty strings"
    )
    assert results["no-package"]["detail"] == "package must be a non-empty string"


DRIVER = """\
import importlib.util, io, json, sys

spec = importlib.util.spec_from_file_location("spack_helper", sys.argv[1])
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
for request in json.loads(open(sys.argv[2]).read()):
    print(json.dumps(helper._handle(request), sort_keys=True))
sys.stdin = io.StringIO("not json")
helper.main()
"""


def test_spack_helper_rejects_malformed_requests(tmp_path):
    requests = [
        {"action": "detect_many", "requests": "not-a-list"},
        {"action": "detect_many", "requests": ["not-a-dict"]},
        {"action": "detect_many", "requests": [{"package": "mpi"}]},
        {
            "action": "detect_many",
            "requests": [{"id": "a", "package": "mpi"}, {"id": "a", "package": "mpi"}],
        },
        {"action": "detect", "package": "mpi"},
        {"action": "canonicalize"},
        {"action": "no-such-action"},
    ]
    (tmp_path / "driver.py").write_text(DRIVER)
    (tmp_path / "requests.json").write_text(json.dumps(requests))
    command = system_external._spack_command()
    helper = command[-1]
    command[-1:] = [
        str(tmp_path / "driver.py"),
        helper,
        str(tmp_path / "requests.json"),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
        env=system_external._spack_environment(),
    )
    lines = completed.stdout.splitlines()
    responses = [json.loads(line) for line in lines[: len(requests)]]

    assert [r.get("detail") for r in responses[:4]] == [
        "detect_many requests must be a list",
        "detect_many request must be a dictionary",
        "detect_many request id must be a non-empty string",
        "detect_many request ids must be unique",
    ]
    assert responses[4] == {
        "status": "ok",
        "detection": {"outcome": "no_applicable_validator", "finders": []},
    }
    assert responses[5] == {"status": "ok", "records": []}
    assert responses[6] == {"status": "error", "detail": "unsupported helper action"}
    final = system_external._framed_response(completed.stdout, SPACK_PREFIX, "helper")
    assert final["status"] == "error"
    assert final["detail"].startswith("JSONDecodeError")


# ---------------------------------------------------------------------------
# _run_spack_helper and _run_spack_batch with canned helper output
# ---------------------------------------------------------------------------


def _completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr=stderr)


@pytest.fixture
def helper_output(monkeypatch):
    """Make subprocess.run return (or raise) ``result`` and record each call."""
    calls = []

    def install(result):
        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            if isinstance(result, BaseException):
                raise result
            return result

        monkeypatch.setattr(system_external.subprocess, "run", fake_run)
        return calls

    return install


def test_run_spack_helper_returns_last_framed_result(helper_output):
    stdout = "\n".join(
        [
            "==> Spack chatter",
            SPACK_PREFIX + json.dumps({"status": "ok", "attempt": 1}),
            SPACK_PREFIX + json.dumps({"status": "ok", "attempt": 2}),
            "trailing output",
        ]
    )
    calls = helper_output(_completed(stdout=stdout))

    assert system_external._run_spack_helper({"action": "canonicalize"}) == {
        "status": "ok",
        "attempt": 2,
    }
    command, kwargs = calls[0]
    assert command == system_external._spack_command()
    assert json.loads(kwargs["input"]) == {"action": "canonicalize"}


@pytest.mark.parametrize(
    "completed, message",
    [
        (_completed(3, stderr="first\nlast line"), "exited with status 3: last line"),
        (_completed(3), "exited with status 3$"),
        (_completed(stdout="no result here"), "did not emit a result"),
        (_completed(stdout=SPACK_PREFIX + "{not json"), "emitted invalid JSON"),
        (
            _completed(stdout=SPACK_PREFIX + '{"status": "error", "detail": "boom"}'),
            "^boom$",
        ),
        (
            _completed(stdout=SPACK_PREFIX + '{"status": "error"}'),
            "^Spack helper failed$",
        ),
        (_completed(stdout=SPACK_PREFIX + "[1, 2]"), "^Spack helper failed$"),
    ],
)
def test_run_spack_helper_failures(helper_output, completed, message):
    helper_output(completed)

    with pytest.raises(_SpackHelperError, match=message):
        system_external._run_spack_helper({"action": "detect"})


def test_run_spack_helper_site_purged_leaves_virtualenv(helper_output, monkeypatch):
    monkeypatch.setenv("VIRTUAL_ENV", "/venv")
    monkeypatch.setenv("PATH", "/venv/bin:/usr/bin")
    calls = helper_output(_completed(stdout=SPACK_PREFIX + '{"status": "ok"}'))

    system_external._run_spack_helper({}, site_purged=True)

    command, kwargs = calls[0]
    assert command[:2] == ["/bin/bash", "-lc"]
    assert command[3:] == ["benchpark-system-external"] + (
        system_external._spack_command()
    )
    assert kwargs["env"]["PATH"] == "/usr/bin"
    assert "VIRTUAL_ENV" not in kwargs["env"]


def test_run_spack_batch_without_requests_skips_spack(monkeypatch):
    monkeypatch.setattr(
        system_external, "_run_spack_helper", lambda *a, **k: pytest.fail("ran Spack")
    )

    assert system_external._run_spack_batch([]) == {}


@pytest.mark.parametrize(
    "requests, message",
    [
        (["not-a-dict"], "must be a dictionary"),
        ([{"package": "cmake"}], "id must be a non-empty string"),
        ([{"id": "a"}, {"id": "a"}], "ids must be unique"),
    ],
)
def test_run_spack_batch_validates_requests(monkeypatch, requests, message):
    monkeypatch.setattr(
        system_external, "_run_spack_helper", lambda *a, **k: pytest.fail("ran Spack")
    )

    with pytest.raises(_SpackHelperError, match=message):
        system_external._run_spack_batch(requests)


def _batch_response(monkeypatch, response):
    calls = []

    def fake_helper(request, **kwargs):
        calls.append((request, kwargs))
        if isinstance(response, BaseException):
            raise response
        return response

    monkeypatch.setattr(system_external, "_run_spack_helper", fake_helper)
    return calls


FAILED = {"outcome": "failed", "finders": []}


def test_run_spack_batch_maps_detections_to_requests(monkeypatch):
    calls = _batch_response(
        monkeypatch,
        {
            "status": "ok",
            "detections": [
                {"id": "b", "detection": FAILED},
                {"id": "a", "detection": FAILED},
            ],
        },
    )

    results = system_external._run_spack_batch([{"id": "a"}, {"id": "b"}])

    assert results == {"a": FAILED, "b": FAILED}
    request, kwargs = calls[0]
    assert request == {"action": "detect_many", "requests": [{"id": "a"}, {"id": "b"}]}
    assert kwargs == {
        "timeout": system_external._SPACK_BATCH_TIMEOUT_SECONDS,
        "site_purged": True,
    }


@pytest.mark.parametrize(
    "response, message",
    [
        (subprocess.TimeoutExpired("spack", 600), "timed out after 600 seconds"),
        (OSError("no such file"), "could not start: no such file"),
        ({"status": "ok"}, "returned no detection results"),
        ({"detections": ["x"]}, "malformed detection result"),
        ({"detections": [{"id": 1}]}, "malformed request id"),
        ({"detections": [{"id": "zzz", "detection": FAILED}]}, "unknown request id"),
        (
            {
                "detections": [
                    {"id": "a", "detection": FAILED},
                    {"id": "a", "detection": FAILED},
                ]
            },
            "duplicate request id",
        ),
        ({"detections": []}, "omitted a requested package result"),
    ],
)
def test_run_spack_batch_rejects_bad_responses(monkeypatch, response, message):
    _batch_response(monkeypatch, response)

    with pytest.raises(_SpackHelperError, match=message):
        system_external._run_spack_batch([{"id": "a"}])


def _finder(status="success", name="executables", records=()):
    return {"name": name, "status": status, "records": list(records)}


@pytest.mark.parametrize(
    "detection, message",
    [
        ("not-a-dict", "malformed package result"),
        ({"outcome": "maybe", "finders": []}, "invalid package outcome"),
        ({"outcome": "success", "finders": "x"}, "malformed finder records"),
        ({"outcome": "success", "finders": []}, "no finder outcomes"),
        ({"outcome": "failed", "finders": ["x"]}, "malformed finder result"),
        (
            {"outcome": "failed", "finders": [_finder(name="")]},
            "malformed finder result",
        ),
        (
            {"outcome": "failed", "finders": [_finder("maybe")]},
            "invalid finder outcome",
        ),
        (
            {"outcome": "failed", "finders": [{**_finder(), "records": "x"}]},
            "malformed finder records",
        ),
        (
            {"outcome": "success", "finders": [_finder("failed")]},
            "inconsistent finder outcomes",
        ),
        (
            {"outcome": "no_applicable_validator", "finders": [_finder()]},
            "inconsistent finder outcomes",
        ),
    ],
)
def test_validate_batched_detection_rejects(detection, message):
    with pytest.raises(_SpackHelperError, match=message):
        system_external._validate_batched_detection(detection)


def test_validate_batched_detection_accepts_consistent_result():
    detection = {
        "outcome": "success",
        "finders": [_finder(), _finder("not_applicable", name="libraries")],
    }

    assert system_external._validate_batched_detection(detection) is detection
    assert system_external._failed_spack_detection("why") == {
        "outcome": "failed",
        "detail": "why",
        "finders": [],
    }


def test_run_bounded_jobs_maps_failures():
    def double(value):
        if value < 0:
            raise ValueError("negative")
        return value * 2

    jobs = [("a", (1,)), ("b", (-1,)), ("c", (3,))]
    results = system_external._run_bounded_jobs(jobs, double, lambda e: f"failed: {e}")

    assert results == {"a": 2, "b": "failed: negative", "c": 6}
    assert system_external._run_bounded_jobs([], double, str) == {}


# ---------------------------------------------------------------------------
# Declared externals
# ---------------------------------------------------------------------------


def test_extract_declared_externals_reports_each_problem():
    packages = {
        "string-config": "ignored",
        "no-externals": {"buildable": False},
        "not-a-list": {"externals": {"spec": "cmake@3.27.0"}},
        "cmake": {
            "externals": [
                "not-a-dict",
                {"spec": "cmake@3.27.0", "prefix": "/usr", "flags": {}},
                {"prefix": "/usr"},
                {"spec": "cmake@3.27.0", "prefix": ""},
                {"spec": "cmake@3.27.0", "modules": []},
                {"spec": "cmake@3.27.0", "modules": ["cmake/3.27.0", 3]},
                {"spec": "cmake@3.27.0"},
                {
                    "spec": "cmake@3.27.0",
                    "prefix": "/usr//local/",
                    "extra_attributes": {},
                },
                {"spec": "cmake@3.28.0", "modules": ["cmake/3.28.0"]},
            ]
        },
    }

    externals = system_external._extract_declared_externals(packages)

    assert [(e.package, e.invalid_detail) for e in externals[:8]] == [
        ("not-a-list", "externals must be a list"),
        ("cmake", "external must be a dictionary"),
        ("cmake", "unsupported external fields: flags"),
        ("cmake", "spec must be a non-empty string"),
        ("cmake", "prefix must be a non-empty string"),
        ("cmake", "modules must be a non-empty list of strings"),
        ("cmake", "modules must be a non-empty list of strings"),
        ("cmake", "external declares neither prefix nor modules"),
    ]
    assert externals[0].raw_spec == "cmake@3.27.0"
    assert externals[3].raw_prefix == "/usr" and externals[3].raw_spec is None
    with_prefix, with_modules = externals[8:]
    assert (with_prefix.prefix, with_prefix.extra_attributes) == ("/usr/local", True)
    assert with_prefix.invalid_detail is None
    assert (with_modules.prefix, with_modules.modules) == (None, ("cmake/3.28.0",))
    assert system_external._invalid_declaration_reason(externals[1]) == (
        "INVALID_DECLARATION"
    )
    assert system_external._invalid_declaration_reason(
        replace(externals[1], unrepresentable=True)
    ) == ("UNREPRESENTABLE_SPEC")


def _declared(package, spec, **fields):
    return _External(
        package=package,
        raw_spec=spec,
        raw_prefix="/usr",
        prefix="/usr",
        modules=(),
        **fields,
    )


def _canonical_records(monkeypatch, records):
    requests = []

    def fake_helper(request, **kwargs):
        requests.append(request)
        return {"status": "ok", "records": records}

    monkeypatch.setattr(system_external, "_run_spack_helper", fake_helper)
    return requests


def test_canonicalize_declared_externals(monkeypatch):
    declarations = [
        _declared("cmake", "cmake@3.27.0"),
        _declared("zlib", "zlib@@"),
        _declared("gcc", "gcc@13"),
        _declared("python", "py-other@3.12"),
        _declared("ninja", "ninja@1.12"),
        _declared("hwloc", "hwloc@2.11"),
        _declared("mpich", None, invalid_detail="spec must be a non-empty string"),
    ]
    requests = _canonical_records(
        monkeypatch,
        [
            {
                "id": 0,
                "status": "ok",
                "package": "cmake",
                "spec": "cmake@=3.27.0",
                "version": "3.27.0",
            },
            {"id": 1, "status": "invalid", "detail": "bad spec"},
            {"id": 2, "status": "unrepresentable", "detail": "lossy"},
            {
                "id": 3,
                "status": "ok",
                "package": "py-other",
                "spec": "py-other@=3.12",
                "version": "3.12",
            },
            {
                "id": 4,
                "status": "ok",
                "package": "ninja",
                "spec": "ninja@=1.12",
                "version": "",
            },
            {"id": 5, "status": "invalid"},
        ],
    )

    cmake, zlib, gcc, python, ninja, hwloc, mpich = (
        system_external._canonicalize_declared_externals(declarations)
    )

    # Declarations that are already invalid are not sent to Spack
    assert [item["id"] for item in requests[0]["specs"]] == [0, 1, 2, 3, 4, 5]
    assert (cmake.spec, cmake.version, cmake.invalid_detail) == (
        "cmake@=3.27.0",
        "3.27.0",
        None,
    )
    assert (zlib.invalid_detail, zlib.unrepresentable) == ("bad spec", False)
    assert (gcc.invalid_detail, gcc.unrepresentable) == ("lossy", True)
    assert "disagrees with parsed spec root 'py-other'" in python.invalid_detail
    assert (
        ninja.invalid_detail == "canonical spec and version must be non-empty strings"
    )
    assert hwloc.invalid_detail == "Spack could not canonicalize the spec"
    assert mpich is declarations[-1]
    assert system_external._with_canonical_spec(mpich, "x", "y") is mpich


def test_canonicalize_skips_spack_without_valid_declarations(monkeypatch):
    monkeypatch.setattr(
        system_external, "_run_spack_helper", lambda *a, **k: pytest.fail("ran Spack")
    )
    invalid = [_declared("cmake", None, invalid_detail="missing spec")]

    assert system_external._canonicalize_declared_externals(invalid) == invalid


@pytest.mark.parametrize(
    "records, message",
    [
        (None, "returned no canonicalization records"),
        ([{"id": 0}, {"id": 0}], "duplicate canonicalization ids"),
        ([{"id": 7}], "omitted a canonicalization record"),
    ],
)
def test_canonicalize_rejects_bad_records(monkeypatch, records, message):
    _canonical_records(monkeypatch, records)

    with pytest.raises(_SpackHelperError, match=message):
        system_external._canonicalize_declared_externals(
            [_declared("cmake", "cmake@3.27.0")]
        )


# ---------------------------------------------------------------------------
# Module validation
# ---------------------------------------------------------------------------


def test_validate_module_sequence_requires_modules():
    with pytest.raises(ValueError, match="requires a declared module sequence"):
        system_external._validate_module_sequence([])


def _module_line(**result):
    payload = {
        "outcome": "valid",
        "failed_module": None,
        "detail": None,
        "loaded_modules": ["cmake/3.27.0"],
        "spack_status": None,
    }
    payload.update(result)
    return MODULE_PREFIX + json.dumps(payload)


@pytest.mark.parametrize(
    "completed, detail",
    [
        (
            subprocess.TimeoutExpired("bash", 60),
            "module validator timed out after 60 seconds",
        ),
        (
            _completed(1, stderr="noise\nmodule: command not found"),
            "module: command not found",
        ),
        (_completed(1), "module validator exited with status 1"),
        (_completed(stdout="nothing framed"), "module validator did not emit a result"),
        (
            _completed(stdout=_module_line(outcome="maybe")),
            "module validator returned an invalid outcome",
        ),
    ],
)
def test_validate_module_sequence_failures(helper_output, completed, detail):
    helper_output(completed)

    result = system_external._validate_module_sequence(["cmake/3.27.0"])

    assert result["outcome"] == "validator_failed"
    assert result["detail"] == detail
    assert result["loaded_modules"] == []


def test_validate_module_sequence_returns_module_result(helper_output):
    calls = helper_output(_completed(stdout=_module_line()))

    result = system_external._validate_module_sequence(["cmake/3.27.0", "gcc/13"])

    assert result["outcome"] == "valid"
    command, kwargs = calls[0]
    assert command[-2:] == ["cmake/3.27.0", "gcc/13"]
    assert "BENCHPARK_SPACK_REQUEST" not in kwargs["env"]


@pytest.mark.parametrize(
    "stdout, spack_error",
    [
        (
            _module_line(spack_status="1"),
            "Spack helper failed in the module-loaded child",
        ),
        (
            _module_line(spack_status="0")
            + "\n"
            + SPACK_PREFIX
            + '{"status": "error", "detail": "nope"}',
            "nope",
        ),
        (_module_line(spack_status="0"), "Spack helper did not emit a result"),
    ],
)
def test_validate_module_sequence_hybrid_spack_errors(
    helper_output, stdout, spack_error
):
    helper_output(_completed(stdout=stdout))

    result = system_external._validate_module_sequence(
        ["cmake/3.27.0"], hybrid_request={"action": "detect"}
    )

    assert result["outcome"] == "valid"
    assert result["spack_error"] == spack_error


def test_validate_module_sequence_hybrid_skips_spack_when_module_fails(helper_output):
    helper_output(
        _completed(stdout=_module_line(outcome="not_found", spack_status="1"))
    )

    result = system_external._validate_module_sequence(
        ["cmake/3.27.0"], hybrid_request={"action": "detect"}
    )

    assert result["outcome"] == "not_found"
    assert "spack_error" not in result


def test_lmod_required_only_when_unavailable_everywhere():
    validations = [("a", ("x",), None), ("b", ("y",), None)]
    unavailable = {
        "outcome": "validator_failed",
        "detail": "module command unavailable",
    }

    system_external._require_lmod_when_globally_unavailable([], {})
    system_external._require_lmod_when_globally_unavailable(
        validations, {"a": unavailable, "b": {"outcome": "valid"}}
    )
    with pytest.raises(system_external._ValidatorInfrastructureError, match="Lmod"):
        system_external._require_lmod_when_globally_unavailable(
            validations, {"a": unavailable, "b": unavailable}
        )


MODULE_DECLARATION = _External(
    package="cmake",
    raw_spec="cmake@3.27.0",
    raw_prefix=None,
    prefix=None,
    modules=("cmake/3.27.0",),
)


@pytest.mark.parametrize(
    "module_result, state, reason",
    [
        ({"outcome": "valid"}, "VALID", None),
        ({"outcome": "not_found"}, "NOT_FOUND", None),
        ({"outcome": "module_load_failed"}, "REVIEW_REQUIRED", "MODULE_LOAD_FAILED"),
        ({"outcome": "validator_failed"}, "REVIEW_REQUIRED", "VALIDATOR_FAILED"),
    ],
)
def test_validate_module_external_states(module_result, state, reason):
    result = system_external._validate_module_external(
        MODULE_DECLARATION,
        {
            "loaded_modules": ["cmake/3.27.0", "gcc/13"],
            "failed_module": "cmake/3.27.0",
            "detail": "why",
            **module_result,
        },
    )

    assert (result.state, result.reason) == (state, reason)
    assert result.validation_basis == "module_sequence"
    assert result.loaded_modules == ("cmake/3.27.0", "gcc/13")
    assert (result.failed_module, result.detail) == ("cmake/3.27.0", "why")


def test_validate_module_external_sanitizes_malformed_result():
    result = system_external._validate_module_external(
        MODULE_DECLARATION,
        {"outcome": "valid", "loaded_modules": "x", "failed_module": 3, "detail": ""},
    )

    assert (result.loaded_modules, result.failed_module, result.detail) == (
        (),
        None,
        None,
    )


def test_validate_module_external_rejects_invalid_declaration():
    invalid = replace(MODULE_DECLARATION, invalid_detail="bad")

    result = system_external._validate_module_external(invalid, {"outcome": "valid"})

    assert (result.state, result.reason) == ("REVIEW_REQUIRED", "INVALID_DECLARATION")


@pytest.mark.parametrize(
    "module_result, state, detail",
    [
        ({"outcome": "not_found"}, "NOT_FOUND", None),
        (
            {"outcome": "valid", "spack_error": "spack broke"},
            "REVIEW_REQUIRED",
            "spack broke",
        ),
        (
            {"outcome": "valid"},
            "REVIEW_REQUIRED",
            "module validation completed without a Spack result",
        ),
    ],
)
def test_validate_hybrid_external_needs_spack_result(module_result, state, detail):
    result = system_external._validate_hybrid_external(
        MODULE_DECLARATION, module_result
    )

    assert (result.state, result.detail) == (state, detail)
    if state == "REVIEW_REQUIRED":
        assert result.reason == "VALIDATOR_FAILED"
        assert result.validation_basis == "module_sequence+spack_prefix"


# ---------------------------------------------------------------------------
# run() and the report
# ---------------------------------------------------------------------------

DECLARED = replace(MODULE_DECLARATION, spec="cmake@=3.27.0", version="3.27.0")
OBSERVED = _External(
    package="cmake",
    raw_spec="cmake@3.28.0",
    raw_prefix="/opt/cmake",
    prefix="/opt/cmake",
    modules=(),
    spec="cmake@=3.28.0",
    version="3.28.0",
    observed_by=("executables",),
    observation_conflict="two prefixes",
)
INVALID = _External(
    package="cmake",
    raw_spec=None,
    raw_prefix=None,
    prefix=None,
    modules=(),
    invalid_detail="spec must be a non-empty string",
)


def _package_result(validator_outcome="SUCCESS"):
    return _PackageResult(
        package="cmake",
        declarations=(
            _DeclarationResult(
                DECLARED,
                "VALID",
                detail="loaded",
                failed_module="cmake/3.27.0",
                validation_basis="module_sequence",
                evidence=(OBSERVED,),
                loaded_modules=("cmake/3.27.0", "gcc/13.2.0"),
            ),
            _DeclarationResult(
                INVALID, "REVIEW_REQUIRED", reason="INVALID_DECLARATION"
            ),
        ),
        candidates=(
            _CandidateResult(OBSERVED, matched=True),
            _CandidateResult(OBSERVED, classification="ADDITIONAL_VERSION"),
            _CandidateResult(replace(OBSERVED, observed_by=())),
        ),
        validator_outcome=validator_outcome,
        validator_detail="2 records",
        proposals=(
            _Proposal(
                "ADDITIONAL_VERSION", None, candidate=OBSERVED, source_mutable=True
            ),
            _Proposal(
                "REPLACEMENT", DECLARED, candidate=OBSERVED, source_reason="shared"
            ),
            _Proposal("REPLACEMENT", DECLARED, also_changes=("dane", "ruby")),
        ),
    )


def test_report_reconciliation(capsys):
    system_external._report_reconciliation("generic-x86", [_package_result()])

    out = capsys.readouterr().out
    observed = (
        "cmake cmake@=3.28.0 | prefix=/opt/cmake | observation conflict=two prefixes"
    )
    for line in [
        "External reconciliation for generic-x86",
        "cmake (broad Spack detection: SUCCESS: 2 records)",
        "  VALID: cmake cmake@=3.27.0 | modules=cmake/3.27.0; basis=module_sequence",
        "    failed module: cmake/3.27.0",
        "    detail: loaded",
        "    loaded modules: cmake/3.27.0, gcc/13.2.0",
        "    automatically loaded modules: gcc/13.2.0",
        f"    evidence: {observed}",
        "  REVIEW_REQUIRED [INVALID_DECLARATION]: cmake <unrepresentable spec>"
        " | detail=spec must be a non-empty string",
        f"  MATCHED: {observed}; observed by=executables",
        f"  ADDITIONAL_VERSION: {observed}; observed by=executables",
        f"  OBSERVED: {observed}",
        f"  proposal ADDITIONAL_VERSION [writable]: cmake -> {observed}",
        "  proposal REPLACEMENT [report-only]: cmake cmake@=3.27.0"
        f" | modules=cmake/3.27.0 -> {observed} (shared)",
        "  proposal REPLACEMENT [report-only]: cmake cmake@=3.27.0"
        " | modules=cmake/3.27.0 (also changes cluster=dane, ruby)",
    ]:
        assert line in out.splitlines()


def _run_args(**kwargs):
    return argparse.Namespace(spec=["generic-x86"], **kwargs)


@pytest.fixture
def reconciled(monkeypatch):
    """Skip real detection; reconciliation returns the canned package result."""
    results = [_package_result()]
    monkeypatch.setattr(
        system_external, "_reconcile_system_externals", lambda system: results
    )
    monkeypatch.setattr(
        system_external,
        "_with_source_proposals",
        lambda spec, package_results, source: package_results,
    )
    return results


def test_run_reports_and_sets_exit_status(reconciled, monkeypatch, capsys):
    assert system_external.run(_run_args()) == 0
    heading = capsys.readouterr().out.splitlines()[0]
    assert heading.startswith("External reconciliation for ")
    assert "generic-x86" in heading

    reconciled[0] = _package_result("VALIDATOR_FAILED")
    assert system_external.run(_run_args()) == 1


def test_run_reports_untrustworthy_reconciliation(monkeypatch, capsys):
    def fail(system):
        raise RuntimeError("Spack exploded")

    monkeypatch.setattr(system_external, "_reconcile_system_externals", fail)

    assert system_external.run(_run_args()) == 1
    assert "could not produce a trustworthy result: Spack exploded" in (
        capsys.readouterr().out
    )


def test_run_propose_without_readable_source(reconciled, monkeypatch, capsys):
    monkeypatch.setattr(
        system_external,
        "_read_system_source",
        lambda spec: (None, None, None, "permission denied"),
    )

    assert system_external.run(_run_args(propose=True)) == 0
    assert "Source mutation is unavailable: permission denied" in (
        capsys.readouterr().out
    )
    assert system_external.run(_run_args(apply=True)) == 1


@pytest.mark.parametrize(
    "outcome, expected, status",
    [
        ((None, True), "Post-apply external reconciliation", 0),
        ((None, False), "No eligible source changes were applied.", 0),
        (
            system_external._ApplyVerificationError("verification mismatch"),
            "External reconciliation apply failed: verification mismatch",
            1,
        ),
    ],
)
def test_run_apply(reconciled, monkeypatch, capsys, outcome, expected, status):
    def apply(system_spec, package_results, source_path, source_bytes, source):
        assert source_path.name == "system.py" and "class" in source
        if isinstance(outcome, Exception):
            raise outcome
        return package_results, outcome[1]

    monkeypatch.setattr(system_external, "_apply_source_proposals", apply)

    assert system_external.run(_run_args(apply=True)) == status
    assert expected in capsys.readouterr().out


def test_read_system_source(monkeypatch, tmp_path):
    system_spec = benchpark.spec.SystemSpec("generic-x86").concretize()

    path, raw, text, error = system_external._read_system_source(system_spec)
    assert path.parts[-2:] == ("generic-x86", "system.py")
    assert raw.decode("utf-8") == text and error is None

    monkeypatch.setattr(
        system_external, "_system_source_path", lambda spec: tmp_path / "missing.py"
    )
    path, raw, text, error = system_external._read_system_source(system_spec)
    assert (raw, text) == (None, None)
    assert "No such file" in error
