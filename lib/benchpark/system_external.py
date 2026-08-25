# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0


import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Optional, Tuple

import benchpark.repo
import benchpark.spec
import benchpark.system
from benchpark.paths import paths

_SPACK_TIMEOUT_SECONDS = 60
_SPACK_BATCH_TIMEOUT_SECONDS = 600
_VALIDATOR_CONCURRENCY = 4
_SPACK_RESULT_PREFIX = "BENCHPARK_EXTERNAL_RESULT="
_MODULE_RESULT_PREFIX = "BENCHPARK_EXTERNAL_MODULE_RESULT="
_NOT_FOUND_MARKER = "# benchpark: external-status=not-found"
_SPACK_SITE_PURGED_SHELL = """
if type module >/dev/null 2>&1; then
    module --force purge || exit $?
fi
exec "$@"
"""
_MODULE_RESULT_EMITTER = (
    "import json, sys; "
    "loaded=[item for item in sys.argv[4].splitlines() "
    "if item and item != 'No modules loaded']; "
    "result={'outcome': sys.argv[1], "
    "'failed_module': sys.argv[2] or None, "
    "'detail': sys.argv[3] or None, "
    "'loaded_modules': loaded, "
    "'spack_status': sys.argv[5] or None}; "
    "print('BENCHPARK_EXTERNAL_MODULE_RESULT=' + json.dumps(result, sort_keys=True))"
)
_MODULE_VALIDATION_SHELL = """python_exe=$1
shift

_emit() {
    "$python_exe" -c "$BENCHPARK_EXTERNAL_MODULE_EMITTER" "$1" "$2" "$3" "$4" "$5"
}

_loaded_modules() {
    module -t list 2>&1
}

if ! type module >/dev/null 2>&1; then
    _emit "validator_failed" "" "module command unavailable" "" ""
    exit 0
fi

module --force purge >/dev/null 2>&1
purge_status=$?
if [ "$purge_status" -ne 0 ]; then
    _emit "validator_failed" "" "module --force purge failed" "" ""
    exit 0
fi

for requested_module in "$@"; do
    module is-avail "$requested_module" >/dev/null 2>&1
    availability_status=$?
    if [ "$availability_status" -ne 0 ]; then
        loaded_modules=$(_loaded_modules)
        if [ "$availability_status" -eq 1 ]; then
            _emit "not_found" "$requested_module" "" "$loaded_modules" ""
        else
            _emit "validator_failed" "$requested_module" "module is-avail failed" "$loaded_modules" ""
        fi
        exit 0
    fi

    module load "$requested_module"
    load_status=$?
    if [ "$load_status" -ne 0 ]; then
        loaded_modules=$(_loaded_modules)
        _emit "module_load_failed" "$requested_module" "module load failed" "$loaded_modules" ""
        exit 0
    fi
done

loaded_modules=$(_loaded_modules)
loaded_status=$?
if [ "$loaded_status" -ne 0 ]; then
    _emit "validator_failed" "" "module list failed" "" ""
    exit 0
fi

spack_status=""
if [ -n "${BENCHPARK_SPACK_REQUEST:-}" ]; then
    printf '%s' "$BENCHPARK_SPACK_REQUEST" | "$BENCHPARK_SPACK_EXECUTABLE" python -c "$BENCHPARK_SPACK_CODE"
    spack_status=$?
fi
_emit "valid" "" "" "$loaded_modules" "$spack_status"
"""

# This is deliberately compatible with the Python used by `spack python`.
# It only parses, canonicalizes, and invokes Spack's existing raw finders.
_SPACK_HELPER = r'''
import json
import sys

import spack.repo
import spack.spec
from spack.detection.path import ExecutablesFinder, LibrariesFinder


_RESULT_PREFIX = "BENCHPARK_EXTERNAL_RESULT="


def _error_detail(error):
    return "{0}: {1}".format(error.__class__.__name__, error)


def _canonical_record(spec_like, raw_spec, record_id):
    result = {"id": record_id, "raw_spec": raw_spec}
    try:
        spec = spack.spec.parse_with_version_concrete(spec_like)
        canonical = str(spec)
        round_trip = spack.spec.parse_with_version_concrete(canonical)
        if not spec.eq_dag(round_trip):
            result.update(
                {
                    "status": "unrepresentable",
                    "detail": "canonical spec does not preserve Spack semantics",
                }
            )
            return result
        result.update(
            {
                "status": "ok",
                "package": spec.name,
                "spec": canonical,
                "version": str(spec.version),
            }
        )
    except Exception as error:
        result.update({"status": "invalid", "detail": _error_detail(error)})
    return result


def _parse_declared_specs(specs):
    return [
        (item, spack.spec.parse_with_version_concrete(item)) for item in specs
    ]


def _detected_record(spec, record_id, declared_specs=()):
    normalized_spec = spack.spec.parse_with_version_concrete(spec)
    result = _canonical_record(normalized_spec, str(spec), record_id)
    prefix = spec.external_path
    result["prefix"] = str(prefix) if prefix is not None else None
    result["modules"] = list(spec.external_modules or [])
    if result.get("status") == "ok":
        result["satisfies"] = [
            raw_spec
            for raw_spec, declared_spec in declared_specs
            if normalized_spec.satisfies(declared_spec)
        ]
    return result


def _run_finder(
    name,
    finder,
    package,
    package_class,
    repository,
    initial_guess,
    declared_specs,
):
    try:
        patterns = finder.search_patterns(pkg=package_class)
    except Exception as error:
        return {
            "name": name,
            "status": "failed",
            "detail": _error_detail(error),
            "records": [],
        }
    if not patterns:
        return {"name": name, "status": "not_applicable", "records": []}
    try:
        detected = finder.find(
            pkg_name=package, repository=repository, initial_guess=initial_guess
        )
        return {
            "name": name,
            "status": "success",
            "records": [
                _detected_record(spec, index, declared_specs)
                for index, spec in enumerate(detected)
            ],
        }
    except Exception as error:
        return {
            "name": name,
            "status": "failed",
            "detail": _error_detail(error),
            "records": [],
        }


def _detect(request):
    package = request.get("package")
    initial_guess = request.get("initial_guess")
    raw_declared_specs = request.get("declared_specs", [])
    if not isinstance(package, str) or not package:
        return {
            "outcome": "failed",
            "detail": "package must be a non-empty string",
            "finders": [],
        }
    if initial_guess is not None and not isinstance(initial_guess, list):
        return {
            "outcome": "failed",
            "detail": "initial_guess must be a list or null",
            "finders": [],
        }
    if not isinstance(raw_declared_specs, list) or not all(
        isinstance(item, str) and item for item in raw_declared_specs
    ):
        return {
            "outcome": "failed",
            "detail": "declared_specs must be a list of non-empty strings",
            "finders": [],
        }
    try:
        declared_specs = _parse_declared_specs(raw_declared_specs)
        if spack.repo.PATH.is_virtual(package):
            return {"outcome": "no_applicable_validator", "finders": []}
        repository = spack.repo.PATH.ensure_unwrapped()
        package_class = repository.get_pkg_class(package)
    except Exception as error:
        return {"outcome": "failed", "detail": _error_detail(error), "finders": []}

    finders = [
        _run_finder(
            "executables",
            ExecutablesFinder(),
            package,
            package_class,
            repository,
            initial_guess,
            declared_specs,
        ),
        _run_finder(
            "libraries",
            LibrariesFinder(),
            package,
            package_class,
            repository,
            initial_guess,
            declared_specs,
        ),
    ]
    applicable = [item for item in finders if item["status"] != "not_applicable"]
    if not applicable:
        outcome = "no_applicable_validator"
    elif any(item["status"] == "failed" for item in applicable):
        outcome = "failed"
    else:
        outcome = "success"
    return {"outcome": outcome, "finders": finders}


def _detect_many(request):
    requests = request.get("requests")
    if not isinstance(requests, list):
        return {
            "status": "error",
            "detail": "detect_many requests must be a list",
        }

    seen_ids = set()
    results = []
    for item in requests:
        if not isinstance(item, dict):
            return {
                "status": "error",
                "detail": "detect_many request must be a dictionary",
            }
        request_id = item.get("id")
        if not isinstance(request_id, str) or not request_id:
            return {
                "status": "error",
                "detail": "detect_many request id must be a non-empty string",
            }
        if request_id in seen_ids:
            return {
                "status": "error",
                "detail": "detect_many request ids must be unique",
            }
        seen_ids.add(request_id)
        try:
            detection = _detect(item)
        except Exception as error:
            detection = {
                "outcome": "failed",
                "detail": _error_detail(error),
                "finders": [],
            }
        results.append({"id": request_id, "detection": detection})
    return {"status": "ok", "detections": results}


def _handle(request):
    action = request.get("action")
    if action == "canonicalize":
        records = []
        for item in request.get("specs", []):
            records.append(
                _canonical_record(item.get("spec"), item.get("spec"), item.get("id"))
            )
        return {"status": "ok", "records": records}
    if action == "detect":
        return {"status": "ok", "detection": _detect(request)}
    if action == "detect_many":
        return _detect_many(request)
    return {"status": "error", "detail": "unsupported helper action"}


def main():
    try:
        request = json.load(sys.stdin)
        result = _handle(request)
    except Exception as error:
        result = {"status": "error", "detail": _error_detail(error)}
    sys.stdout.write(_RESULT_PREFIX + json.dumps(result, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
'''


class _SpackHelperError(RuntimeError):
    pass


class _ValidatorInfrastructureError(RuntimeError):
    pass


@dataclass(frozen=True)
class _External:
    """A declared or detected external before reconciliation."""

    package: str
    raw_spec: Optional[str]
    raw_prefix: Optional[str]
    prefix: Optional[str]
    modules: Tuple[str, ...]
    extra_attributes: bool = False
    spec: Optional[str] = None
    version: Optional[str] = None
    invalid_detail: Optional[str] = None
    unrepresentable: bool = False
    observed_by: Tuple[str, ...] = ()
    satisfies_specs: Tuple[str, ...] = ()
    observation_conflict: Optional[str] = None


@dataclass(frozen=True)
class _DeclarationResult:
    external: _External
    state: str
    reason: Optional[str] = None
    detail: Optional[str] = None
    failed_module: Optional[str] = None
    matched_candidate: Optional[_External] = None
    validation_basis: Optional[str] = None
    evidence: Tuple[_External, ...] = ()
    loaded_modules: Tuple[str, ...] = ()


@dataclass(frozen=True)
class _CandidateResult:
    external: _External
    classification: Optional[str] = None
    matched: bool = False


@dataclass(frozen=True)
class _Proposal:
    """One logical reconciliation change and its source-write eligibility."""

    action: str
    declaration: Optional[_External]
    candidate: Optional[_External] = None
    source_mutable: bool = False
    source_reason: Optional[str] = None


@dataclass(frozen=True)
class _PackageResult:
    package: str
    declarations: Tuple[_DeclarationResult, ...]
    candidates: Tuple[_CandidateResult, ...]
    validator_outcome: Optional[str] = None
    validator_detail: Optional[str] = None
    proposals: Tuple[_Proposal, ...] = ()


@dataclass
class _ReconciliationWork:
    """Mutable declaration state used only while reconciling one package."""

    external: _External
    state: Optional[str] = None
    reason: Optional[str] = None
    detail: Optional[str] = None
    failed_module: Optional[str] = None
    matched_candidate: Optional[_External] = None
    validation_basis: Optional[str] = None
    evidence: Tuple[_External, ...] = ()
    loaded_modules: Tuple[str, ...] = ()


class _ApplyVerificationError(RuntimeError):
    pass


def _normalize_prefix(prefix):
    """Normalize representational path noise without consulting the filesystem."""

    return os.path.normpath(prefix)


def _invalid_external(package, entry, detail):
    raw_spec = entry.get("spec") if isinstance(entry, dict) else None
    raw_prefix = entry.get("prefix") if isinstance(entry, dict) else None
    return _External(
        package=package,
        raw_spec=raw_spec if isinstance(raw_spec, str) else None,
        raw_prefix=raw_prefix if isinstance(raw_prefix, str) else None,
        prefix=None,
        modules=(),
        extra_attributes=isinstance(entry, dict) and "extra_attributes" in entry,
        invalid_detail=detail,
    )


def _invalid_declaration_reason(external):
    return "UNREPRESENTABLE_SPEC" if external.unrepresentable else "INVALID_DECLARATION"


def _extract_declared_externals(packages):
    """Extract external declarations without assigning Spack spec semantics."""

    externals: List[_External] = []
    for package, package_config in packages.items():
        if not isinstance(package_config, dict) or "externals" not in package_config:
            continue

        declared = package_config["externals"]
        if not isinstance(declared, list):
            externals.append(
                _invalid_external(package, declared, "externals must be a list")
            )
            continue

        for entry in declared:
            if not isinstance(entry, dict):
                externals.append(
                    _invalid_external(package, entry, "external must be a dictionary")
                )
                continue

            unknown_fields = set(entry) - {
                "spec",
                "prefix",
                "modules",
                "extra_attributes",
            }
            if unknown_fields:
                fields = ", ".join(sorted(unknown_fields))
                externals.append(
                    _invalid_external(
                        package, entry, f"unsupported external fields: {fields}"
                    )
                )
                continue

            raw_spec = entry.get("spec")
            if not isinstance(raw_spec, str) or not raw_spec:
                externals.append(
                    _invalid_external(package, entry, "spec must be a non-empty string")
                )
                continue

            raw_prefix = entry.get("prefix")
            if "prefix" in entry and (
                not isinstance(raw_prefix, str) or not raw_prefix
            ):
                externals.append(
                    _invalid_external(
                        package, entry, "prefix must be a non-empty string"
                    )
                )
                continue

            raw_modules = entry.get("modules")
            if "modules" in entry and (
                not isinstance(raw_modules, (list, tuple))
                or not raw_modules
                or not all(isinstance(module, str) and module for module in raw_modules)
            ):
                externals.append(
                    _invalid_external(
                        package, entry, "modules must be a non-empty list of strings"
                    )
                )
                continue

            if "prefix" not in entry and "modules" not in entry:
                externals.append(
                    _invalid_external(
                        package, entry, "external declares neither prefix nor modules"
                    )
                )
                continue

            externals.append(
                _External(
                    package=package,
                    raw_spec=raw_spec,
                    raw_prefix=raw_prefix,
                    prefix=_normalize_prefix(raw_prefix)
                    if isinstance(raw_prefix, str)
                    else None,
                    modules=tuple(raw_modules) if raw_modules is not None else (),
                    extra_attributes="extra_attributes" in entry,
                )
            )

    return externals


def _extract_system_externals(system):
    """Extract externals from the fully merged package and compiler configuration."""

    package_section = system.compute_packages_section() or {}
    compiler_section = system.compute_compilers_section() or {}
    merged = benchpark.system.merge_dicts(package_section, compiler_section)
    packages = merged.get("packages", {})
    return _extract_declared_externals(packages)


def _with_canonical_spec(external, spec, version):
    """Attach Spack-provided canonical spec and version strings to an external."""

    if external.invalid_detail is not None:
        return external
    if (
        not isinstance(spec, str)
        or not spec
        or not isinstance(version, str)
        or not version
    ):
        return replace(
            external,
            invalid_detail="canonical spec and version must be non-empty strings",
        )
    return replace(external, spec=spec, version=version)


def _spack_command():
    return [
        str(paths.benchpark_home / "spack/bin/spack"),
        "python",
        "-c",
        "exec(" + repr(_SPACK_HELPER) + ")",
    ]


def _framed_response(stdout, prefix, producer):
    for line in reversed((stdout or "").splitlines()):
        if line.startswith(prefix):
            try:
                return json.loads(line[len(prefix) :])
            except json.JSONDecodeError as error:
                raise _SpackHelperError(f"{producer} emitted invalid JSON") from error
    raise _SpackHelperError(f"{producer} did not emit a result")


def _spack_error_detail(completed):
    output = (completed.stderr or completed.stdout or "").strip()
    if output:
        output = output.splitlines()[-1]
        return f"Spack helper exited with status {completed.returncode}: {output}"
    return f"Spack helper exited with status {completed.returncode}"


def _run_spack_helper(request, *, timeout=_SPACK_TIMEOUT_SECONDS, site_purged=False):
    """Run the private raw-Spack helper without changing Spack configuration."""

    command = _spack_command()
    if site_purged:
        command = [
            "/bin/bash",
            "-lc",
            textwrap.dedent(_SPACK_SITE_PURGED_SHELL),
            "benchpark-system-external",
        ] + command

    environment = os.environ.copy()
    if site_purged:
        virtual_env = environment.pop("VIRTUAL_ENV", None)
        if virtual_env:
            virtual_env_bin = os.path.join(virtual_env, "bin")
            environment["PATH"] = os.pathsep.join(
                entry
                for entry in environment.get("PATH", "").split(os.pathsep)
                if entry != virtual_env_bin
            )
    environment["SPACK_DISABLE_LOCAL_CONFIG"] = "1"
    completed = subprocess.run(
        command,
        input=json.dumps(request, sort_keys=True),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
        env=environment,
    )
    if completed.returncode != 0:
        raise _SpackHelperError(_spack_error_detail(completed))

    response = _framed_response(
        completed.stdout, _SPACK_RESULT_PREFIX, "Spack helper"
    )
    if not isinstance(response, dict) or response.get("status") != "ok":
        detail = response.get("detail") if isinstance(response, dict) else None
        raise _SpackHelperError(detail or "Spack helper failed")
    return response


def _validate_batched_detection(detection):
    if not isinstance(detection, dict):
        raise _SpackHelperError("Spack batch returned a malformed package result")
    outcome = detection.get("outcome")
    if not isinstance(outcome, str) or outcome not in {
        "success",
        "no_applicable_validator",
        "failed",
    }:
        raise _SpackHelperError("Spack batch returned an invalid package outcome")
    finders = detection.get("finders")
    if not isinstance(finders, list):
        raise _SpackHelperError("Spack batch returned malformed finder records")
    if outcome == "success" and not finders:
        raise _SpackHelperError("Spack batch returned no finder outcomes")
    for finder in finders:
        if not isinstance(finder, dict):
            raise _SpackHelperError("Spack batch returned a malformed finder result")
        if not isinstance(finder.get("name"), str) or not finder["name"]:
            raise _SpackHelperError("Spack batch returned a malformed finder result")
        status = finder.get("status")
        if not isinstance(status, str) or status not in {
            "success",
            "not_applicable",
            "failed",
        }:
            raise _SpackHelperError("Spack batch returned an invalid finder outcome")
        if not isinstance(finder.get("records"), list):
            raise _SpackHelperError("Spack batch returned malformed finder records")
    statuses = [finder["status"] for finder in finders]
    if outcome == "success" and "failed" in statuses:
        raise _SpackHelperError("Spack batch returned inconsistent finder outcomes")
    if outcome == "no_applicable_validator" and any(
        status != "not_applicable" for status in statuses
    ):
        raise _SpackHelperError("Spack batch returned inconsistent finder outcomes")
    return detection


def _failed_spack_detection(detail):
    return {"outcome": "failed", "detail": detail, "finders": []}


def _run_spack_batch(requests):
    """Run one site-purged raw-Spack batch and return detections by request id."""

    requests = tuple(requests)
    if not requests:
        return {}
    expected_ids = []
    for request in requests:
        if not isinstance(request, dict):
            raise _SpackHelperError("Spack batch request must be a dictionary")
        request_id = request.get("id")
        if not isinstance(request_id, str) or not request_id:
            raise _SpackHelperError("Spack batch request id must be a non-empty string")
        if request_id in expected_ids:
            raise _SpackHelperError("Spack batch request ids must be unique")
        expected_ids.append(request_id)

    try:
        response = _run_spack_helper(
            {"action": "detect_many", "requests": list(requests)},
            timeout=_SPACK_BATCH_TIMEOUT_SECONDS,
            site_purged=True,
        )
    except subprocess.TimeoutExpired as error:
        raise _SpackHelperError(
            "Spack batch timed out after "
            f"{_SPACK_BATCH_TIMEOUT_SECONDS} seconds"
        ) from error
    except OSError as error:
        raise _SpackHelperError(f"Spack batch could not start: {error}") from error

    detections = response.get("detections")
    if not isinstance(detections, list):
        raise _SpackHelperError("Spack batch returned no detection results")

    expected = set(expected_ids)
    results = {}
    for item in detections:
        if not isinstance(item, dict):
            raise _SpackHelperError("Spack batch returned a malformed detection result")
        request_id = item.get("id")
        if not isinstance(request_id, str):
            raise _SpackHelperError("Spack batch returned a malformed request id")
        if request_id not in expected:
            raise _SpackHelperError("Spack batch returned an unknown request id")
        if request_id in results:
            raise _SpackHelperError("Spack batch returned a duplicate request id")
        results[request_id] = _validate_batched_detection(item.get("detection"))

    if set(results) != expected:
        raise _SpackHelperError("Spack batch omitted a requested package result")
    return results


def _run_bounded_jobs(jobs, worker, failure):
    """Run independent validator jobs with the fixed concurrency bound."""

    jobs = tuple(jobs)
    if not jobs:
        return {}
    results = {}
    with ThreadPoolExecutor(
        max_workers=min(_VALIDATOR_CONCURRENCY, len(jobs))
    ) as executor:
        futures = {
            executor.submit(worker, *arguments): key
            for key, arguments in jobs
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as error:
                results[key] = failure(error)
    return results


def _module_error_detail(completed):
    output = (completed.stderr or "").strip()
    if output:
        return output.splitlines()[-1]
    return f"module validator exited with status {completed.returncode}"


def _validate_module_sequence(modules, hybrid_request=None):
    """Validate one declared module sequence in a force-purged child shell."""

    if not modules:
        raise ValueError("module validation requires a declared module sequence")

    environment = os.environ.copy()
    environment["SPACK_DISABLE_LOCAL_CONFIG"] = "1"
    environment["BENCHPARK_EXTERNAL_MODULE_EMITTER"] = _MODULE_RESULT_EMITTER
    if hybrid_request is not None:
        spack_command = _spack_command()
        environment["BENCHPARK_SPACK_EXECUTABLE"] = spack_command[0]
        environment["BENCHPARK_SPACK_CODE"] = spack_command[-1]
        environment["BENCHPARK_SPACK_REQUEST"] = json.dumps(
            hybrid_request, sort_keys=True
        )

    command = [
        "/bin/bash",
        "-lc",
        _MODULE_VALIDATION_SHELL,
        "benchpark-system-external",
        sys.executable,
    ] + list(modules)
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=_SPACK_TIMEOUT_SECONDS,
            env=environment,
        )
    except subprocess.TimeoutExpired:
        return {
            "outcome": "validator_failed",
            "failed_module": None,
            "detail": (
                f"module validator timed out after {_SPACK_TIMEOUT_SECONDS} seconds"
            ),
            "loaded_modules": [],
            "spack_status": None,
        }
    if completed.returncode != 0:
        return {
            "outcome": "validator_failed",
            "failed_module": None,
            "detail": _module_error_detail(completed),
            "loaded_modules": [],
            "spack_status": None,
        }

    try:
        result = _framed_response(
            completed.stdout, _MODULE_RESULT_PREFIX, "module validator"
        )
    except _SpackHelperError as error:
        return {
            "outcome": "validator_failed",
            "failed_module": None,
            "detail": str(error),
            "loaded_modules": [],
            "spack_status": None,
        }
    if not isinstance(result, dict) or result.get("outcome") not in {
        "valid",
        "not_found",
        "module_load_failed",
        "validator_failed",
    }:
        return {
            "outcome": "validator_failed",
            "failed_module": None,
            "detail": "module validator returned an invalid outcome",
            "loaded_modules": [],
            "spack_status": None,
        }

    if hybrid_request is None or result.get("outcome") != "valid":
        return result

    result = dict(result)
    if str(result.get("spack_status")) not in {"0", "None"}:
        result["spack_error"] = "Spack helper failed in the module-loaded child"
        return result
    try:
        helper_result = _framed_response(
            completed.stdout, _SPACK_RESULT_PREFIX, "Spack helper"
        )
        if helper_result.get("status") != "ok":
            raise _SpackHelperError(
                helper_result.get("detail") or "Spack helper failed"
            )
        result["spack_detection"] = helper_result.get("detection")
    except _SpackHelperError as error:
        result["spack_error"] = str(error)
    return result


def _run_module_validations(validations):
    """Validate independent sequences without touching the parent shell."""

    return _run_bounded_jobs(
        (
            (key, (modules, hybrid_request))
            for key, modules, hybrid_request in validations
        ),
        _validate_module_sequence,
        lambda error: {
            "outcome": "validator_failed",
            "failed_module": None,
            "detail": f"module validator failed: {error}",
            "loaded_modules": [],
            "spack_status": None,
        },
    )


def _require_lmod_when_globally_unavailable(validations, results):
    """Escalate only a proven globally missing module command to exit status 2."""

    if not validations:
        return
    outcomes = [results.get(key) for key, _, _ in validations]
    if outcomes and all(
        isinstance(outcome, dict)
        and outcome.get("outcome") == "validator_failed"
        and outcome.get("detail") == "module command unavailable"
        for outcome in outcomes
    ):
        raise _ValidatorInfrastructureError(
            "Lmod is required for module-backed externals but is unavailable"
        )


def _spack_external(package, record, observed_by):
    if not isinstance(record, dict):
        return _External(
            package=package,
            raw_spec=None,
            raw_prefix=None,
            prefix=None,
            modules=(),
            invalid_detail="Spack returned a malformed detection record",
            observed_by=(observed_by,),
        )

    raw_spec = record.get("raw_spec")
    raw_prefix = record.get("prefix")
    raw_modules = record.get("modules", [])
    raw_satisfies = record.get("satisfies", [])
    base = {
        "package": package,
        "raw_spec": raw_spec if isinstance(raw_spec, str) else None,
        "raw_prefix": raw_prefix if isinstance(raw_prefix, str) else None,
        "observed_by": (observed_by,),
    }
    if record.get("status") != "ok":
        return _External(
            **base,
            prefix=None,
            modules=(),
            invalid_detail=record.get("detail")
            or "Spack returned an unsupported detection record",
            unrepresentable=record.get("status") == "unrepresentable",
        )
    if record.get("package") != package:
        return _External(
            **base,
            prefix=None,
            modules=(),
            invalid_detail=(
                f"Spack detected spec root '{record.get('package')}' for package "
                f"'{package}'"
            ),
        )
    if not isinstance(raw_prefix, str) or not raw_prefix:
        return _External(
            **base,
            prefix=None,
            modules=(),
            invalid_detail="Spack detection did not provide a prefix",
        )
    if not isinstance(raw_modules, list) or not all(
        isinstance(module, str) and module for module in raw_modules
    ):
        return _External(
            **base,
            prefix=None,
            modules=(),
            invalid_detail="Spack detection returned malformed modules",
        )
    if not isinstance(raw_satisfies, list) or not all(
        isinstance(spec, str) and spec for spec in raw_satisfies
    ):
        return _External(
            **base,
            prefix=None,
            modules=(),
            invalid_detail="Spack detection returned malformed satisfaction evidence",
        )

    external = _External(
        **base,
        prefix=_normalize_prefix(raw_prefix),
        modules=tuple(raw_modules),
        satisfies_specs=tuple(raw_satisfies),
    )
    return _with_canonical_spec(external, record.get("spec"), record.get("version"))


def _merge_same_identity_observations(
    existing, observations, *, preserve_existing=False
):
    """Merge provenance for observations already known to share an identity."""

    observations = tuple(observations)
    all_observations = (existing,) + observations
    representative = (
        existing
        if preserve_existing
        else min(all_observations, key=_external_representation_sort_key)
    )
    conflicts = {
        detail
        for observation in all_observations
        for detail in (observation.observation_conflict,)
        if detail
    }
    if any(
        existing.extra_attributes != observation.extra_attributes
        for observation in observations
    ):
        conflicts.add("conflicting auxiliary external metadata")
    return replace(
        representative,
        observed_by=tuple(
            sorted(
                {
                    source
                    for observation in all_observations
                    for source in observation.observed_by
                }
            )
        ),
        satisfies_specs=tuple(
            sorted(
                {
                    spec
                    for observation in all_observations
                    for spec in observation.satisfies_specs
                }
            )
        ),
        observation_conflict="; ".join(sorted(conflicts)) or None,
    )


def _coalesce_observations(observations):
    """Coalesce exact identities while retaining every detection provenance."""

    coalesced = []
    by_identity = {}
    for external in observations:
        if external.invalid_detail is not None:
            coalesced.append(external)
            continue
        identity = _identity_key(external)
        existing_index = by_identity.get(identity)
        if existing_index is None:
            by_identity[identity] = len(coalesced)
            coalesced.append(external)
            continue

        existing = coalesced[existing_index]
        # Raw specs and prefixes may differ only by the lexical noise that is
        # intentionally normalized for identity. Extra attributes are separate
        # metadata and cannot be silently reconciled when they disagree.
        coalesced[existing_index] = _merge_same_identity_observations(
            existing, (external,)
        )
    return tuple(sorted(coalesced, key=_external_sort_key))


def _external_representation_sort_key(external):
    return (
        external.raw_spec or "",
        external.raw_prefix or "",
        external.extra_attributes,
        external.invalid_detail or "",
    )


def _external_sort_key(external):
    return (
        external.package,
        external.spec or "",
        external.prefix or "",
        external.modules,
        external.raw_spec or "",
        external.raw_prefix or "",
        external.invalid_detail or "",
    )


def _merge_validation_provenance(candidates, validations):
    """Retain declaration-bound evidence without adding it to the candidate pool."""

    validation_observations = {}
    for validation in validations:
        for evidence in validation.evidence:
            if evidence.invalid_detail is None:
                validation_observations.setdefault(
                    _identity_key(evidence), []
                ).append(evidence)

    merged = []
    for candidate in candidates:
        observations = validation_observations.get(_identity_key(candidate), [])
        if observations:
            candidate = _merge_same_identity_observations(
                candidate, observations, preserve_existing=True
            )
        merged.append(candidate)
    return tuple(merged)


def _spack_observations(package, detection, observed_by):
    """Convert raw helper records to complete external identities when possible."""

    observations = []
    for finder in detection.get("finders", []):
        if not isinstance(finder, dict):
            continue
        records = finder.get("records", [])
        if not isinstance(records, list):
            observations.append(
                _External(
                    package=package,
                    raw_spec=None,
                    raw_prefix=None,
                    prefix=None,
                    modules=(),
                    invalid_detail="Spack finder returned malformed records",
                    observed_by=(observed_by,),
                )
            )
            continue
        observations.extend(
            _spack_external(package, record, observed_by) for record in records
        )
    return _coalesce_observations(observations)


def _prefix_constraint_matches(declaration, observation):
    return (
        declaration.package == observation.package
        and (
            declaration.spec == observation.spec
            or declaration.spec in observation.satisfies_specs
        )
        and declaration.prefix == observation.prefix
    )


def _validate_spack_prefix(
    declaration,
    detection,
    observed_by,
    *,
    validation_basis,
    loaded_modules=(),
    mismatch_requires_review=False,
):
    if declaration.invalid_detail is not None:
        return _DeclarationResult(
            declaration,
            "REVIEW_REQUIRED",
            reason=_invalid_declaration_reason(declaration),
        )
    loaded_modules = tuple(loaded_modules)

    def declaration_result(state, **fields):
        return _DeclarationResult(
            declaration,
            state,
            validation_basis=validation_basis,
            loaded_modules=loaded_modules,
            **fields,
        )

    if detection.get("outcome") == "no_applicable_validator":
        return declaration_result(
            "REVIEW_REQUIRED",
            reason="NO_APPLICABLE_VALIDATOR",
            detail=detection.get("detail"),
        )
    if detection.get("outcome") != "success":
        return declaration_result(
            "REVIEW_REQUIRED",
            reason="VALIDATOR_FAILED",
            detail=detection.get("detail"),
        )

    observations = _spack_observations(
        declaration.package, detection, observed_by
    )
    if any(item.invalid_detail is not None for item in observations):
        return declaration_result(
            "REVIEW_REQUIRED",
            reason="UNSUPPORTED_DETECTION",
            detail="Spack returned an unsupported detection",
            evidence=observations,
        )
    if any(_prefix_constraint_matches(declaration, item) for item in observations):
        return declaration_result(
            "VALID",
            evidence=observations,
        )
    if observations and mismatch_requires_review:
        return declaration_result(
            "REVIEW_REQUIRED",
            reason="IDENTITY_MISMATCH",
            evidence=observations,
        )
    return declaration_result(
        "NOT_FOUND",
        evidence=observations,
    )


def _validate_prefix_external(declaration, detection):
    """Validate a prefix-only declaration from its targeted Spack pass."""

    return _validate_spack_prefix(
        declaration,
        detection,
        "targeted_prefix_validation",
        validation_basis="spack_prefix",
    )


def _validate_broad_prefix_external(declaration, detection, observations):
    """Return VALID only when a trustworthy broad observation proves a declaration."""

    if detection.get("outcome") == "no_applicable_validator":
        return _DeclarationResult(
            declaration,
            "REVIEW_REQUIRED",
            reason="NO_APPLICABLE_VALIDATOR",
            detail=detection.get("detail"),
            validation_basis="broad_spack_detection",
        )
    if detection.get("outcome") != "success":
        return None
    if any(item.invalid_detail is not None for item in observations):
        return None
    if any(item.observation_conflict for item in observations):
        return None
    if any(_prefix_constraint_matches(declaration, item) for item in observations):
        return _DeclarationResult(
            declaration,
            "VALID",
            validation_basis="broad_spack_detection",
            evidence=observations,
        )
    return None


def _validate_module_external(declaration, module_result):
    """Validate the exact module sequence without inferring package metadata."""

    if declaration.invalid_detail is not None:
        return _DeclarationResult(
            declaration,
            "REVIEW_REQUIRED",
            reason=_invalid_declaration_reason(declaration),
        )

    loaded_modules = module_result.get("loaded_modules", [])
    if not isinstance(loaded_modules, list) or not all(
        isinstance(module, str) for module in loaded_modules
    ):
        loaded_modules = []
    failed_module = module_result.get("failed_module")
    if not isinstance(failed_module, str) or not failed_module:
        failed_module = None
    detail = module_result.get("detail")
    if not isinstance(detail, str) or not detail:
        detail = None
    outcome = module_result.get("outcome")

    def declaration_result(state, **fields):
        return _DeclarationResult(
            declaration,
            state,
            detail=detail,
            failed_module=failed_module,
            validation_basis="module_sequence",
            loaded_modules=tuple(loaded_modules),
            **fields,
        )

    if outcome == "valid":
        return declaration_result("VALID")
    if outcome == "not_found":
        return declaration_result("NOT_FOUND")
    if outcome == "module_load_failed":
        return declaration_result(
            "REVIEW_REQUIRED",
            reason="MODULE_LOAD_FAILED",
        )
    return declaration_result(
        "REVIEW_REQUIRED",
        reason="VALIDATOR_FAILED",
    )


def _validate_hybrid_external(declaration, module_result):
    """Require both the declared module sequence and Spack prefix identity."""

    module_validation = _validate_module_external(declaration, module_result)
    if module_validation.state != "VALID":
        return module_validation
    if module_result.get("spack_error"):
        return replace(
            module_validation,
            state="REVIEW_REQUIRED",
            reason="VALIDATOR_FAILED",
            detail=module_result.get("spack_error"),
            validation_basis="module_sequence+spack_prefix",
        )

    detection = module_result.get("spack_detection")
    if not isinstance(detection, dict):
        return replace(
            module_validation,
            state="REVIEW_REQUIRED",
            reason="VALIDATOR_FAILED",
            detail="module validation completed without a Spack result",
            validation_basis="module_sequence+spack_prefix",
        )
    return _validate_spack_prefix(
        declaration,
        detection,
        "targeted_hybrid_validation",
        validation_basis="module_sequence+spack_prefix",
        loaded_modules=module_validation.loaded_modules,
        mismatch_requires_review=True,
    )


def _canonicalize_declared_externals(declarations):
    """Attach Spack canonical spec data without aborting local declaration errors."""

    eligible = [
        (index, external)
        for index, external in enumerate(declarations)
        if external.invalid_detail is None
    ]
    if not eligible:
        return list(declarations)

    response = _run_spack_helper(
        {
            "action": "canonicalize",
            "specs": [
                {"id": index, "spec": external.raw_spec}
                for index, external in eligible
            ],
        }
    )
    records = response.get("records")
    if not isinstance(records, list):
        raise _SpackHelperError("Spack helper returned no canonicalization records")

    by_id = {}
    for record in records:
        record_id = record.get("id") if isinstance(record, dict) else None
        if record_id in by_id:
            raise _SpackHelperError(
                "Spack helper returned duplicate canonicalization ids"
            )
        by_id[record_id] = record

    canonical = list(declarations)
    for index, external in eligible:
        record = by_id.get(index)
        if not isinstance(record, dict):
            raise _SpackHelperError("Spack helper omitted a canonicalization record")
        if record.get("status") != "ok":
            detail = record.get("detail") or "Spack could not canonicalize the spec"
            canonical[index] = replace(
                external,
                invalid_detail=detail,
                unrepresentable=record.get("status") == "unrepresentable",
            )
            continue

        parsed_package = record.get("package")
        if parsed_package != external.package:
            canonical[index] = replace(
                external,
                invalid_detail=(
                    f"package dictionary key '{external.package}' disagrees with "
                    f"parsed spec root '{parsed_package}'"
                ),
            )
            continue
        canonical[index] = _with_canonical_spec(
            external, record.get("spec"), record.get("version")
        )

    return canonical


def _identity_key(external):
    return external.package, external.spec, external.prefix, external.modules


def _candidate_matches_declaration(declaration, candidate, validation):
    # A prefix-only declaration owns no module identity, so incidental module
    # metadata on a Spack observation cannot turn an exact prefix match into a
    # different external instance.
    if _prefix_only(declaration):
        return _prefix_constraint_matches(declaration, candidate)

    # Module-backed declarations must already have validated their declared
    # sequence before a broad Spack observation can be consumed.
    if validation is None or validation.state != "VALID":
        return False
    if _identity_key(declaration) == _identity_key(candidate):
        return True
    return (
        _hybrid_external(declaration)
        and not candidate.modules
        and _prefix_constraint_matches(declaration, candidate)
    )


def _classify_additional(candidate, declarations):
    same_version = [
        declared for declared in declarations if candidate.version == declared.version
    ]
    if not same_version:
        return "ADDITIONAL_VERSION"
    if any(candidate.spec == declared.spec for declared in same_version):
        return "ADDITIONAL_INSTANCE"
    return "ADDITIONAL_SPEC"


def _reconcile_package(package, declarations, candidates, validation_results=None):
    """Apply deterministic exact matching and cardinality rules for one package."""

    if validation_results is not None and len(validation_results) != len(declarations):
        raise ValueError("validation results must align with package declarations")

    for external in declarations:
        if external.package != package:
            raise ValueError("external package does not match reconciliation package")
        if external.invalid_detail is not None:
            continue
        if external.spec is None or external.version is None:
            raise ValueError("cannot reconcile an external without canonical spec data")

    for external in candidates:
        if external.package != package:
            raise ValueError("external package does not match reconciliation package")
        if external.invalid_detail is not None:
            raise ValueError("cannot reconcile an invalid candidate")
        if external.spec is None or external.version is None:
            raise ValueError("cannot reconcile an external without canonical spec data")

    if validation_results is None:
        validation_results = [None] * len(declarations)

    unmatched_candidates = list(range(len(candidates)))
    matched_candidates = set()
    declaration_work = [
        _ReconciliationWork(external=declaration) for declaration in declarations
    ]

    for declaration_index, declaration in enumerate(declarations):
        work = declaration_work[declaration_index]
        if declaration.invalid_detail is not None:
            work.state = "REVIEW_REQUIRED"
            work.reason = _invalid_declaration_reason(declaration)
            continue

        validation = validation_results[declaration_index]
        if validation is not None:
            if validation.external != declaration:
                raise ValueError("validation result does not match its declaration")
            if validation.state not in {"VALID", "NOT_FOUND", "REVIEW_REQUIRED"}:
                raise ValueError("validation result has an unsupported state")
            work.state = validation.state
            work.reason = validation.reason
            work.detail = validation.detail
            work.failed_module = validation.failed_module
            work.validation_basis = validation.validation_basis
            work.evidence = validation.evidence
            work.loaded_modules = validation.loaded_modules

        if work.state == "REVIEW_REQUIRED":
            continue

        matching_candidate = next(
            (
                candidate_index
                for candidate_index in unmatched_candidates
                if _candidate_matches_declaration(
                    declaration, candidates[candidate_index], validation
                )
            ),
            None,
        )
        if matching_candidate is None:
            continue

        unmatched_candidates.remove(matching_candidate)
        matched_candidates.add(matching_candidate)
        if work.state in {None, "NOT_FOUND"}:
            work.state = "VALID"
            work.reason = None
            work.detail = None
            work.failed_module = None
        work.evidence = _coalesce_observations(
            work.evidence
            + (candidates[matching_candidate],)
        )
        if work.validation_basis is None:
            work.validation_basis = "broad_spack_detection"
        work.matched_candidate = candidates[matching_candidate]

    unmatched_declarations = [
        index
        for index, work in enumerate(declaration_work)
        if work.state in {None, "NOT_FOUND"}
    ]
    unmatched_declaration_count = len(unmatched_declarations)
    unmatched_candidate_count = len(unmatched_candidates)
    if unmatched_candidate_count == 0:
        for declaration_index in unmatched_declarations:
            declaration_work[declaration_index].state = "NOT_FOUND"
    elif unmatched_declaration_count == 1 and unmatched_candidate_count == 1:
        declaration_index = unmatched_declarations[0]
        candidate_index = unmatched_candidates[0]
        declaration_work[declaration_index].state = "REPLACEMENT"
        declaration_work[declaration_index].matched_candidate = candidates[candidate_index]
        matched_candidates.add(candidate_index)
    elif unmatched_declaration_count == 1 and unmatched_candidate_count > 1:
        declaration_work[unmatched_declarations[0]].state = "REVIEW_REQUIRED"
    elif unmatched_declaration_count > 1 and unmatched_candidate_count >= 1:
        for declaration_index in unmatched_declarations:
            declaration_work[declaration_index].state = "REVIEW_REQUIRED"

    candidate_classifications = [None] * len(candidates)
    if unmatched_declaration_count == 0:
        comparable_declarations = [
            declaration
            for declaration in declarations
            if declaration.invalid_detail is None and declaration.spec is not None
        ]
        if comparable_declarations:
            for candidate_index in unmatched_candidates:
                candidate_classifications[candidate_index] = _classify_additional(
                    candidates[candidate_index], comparable_declarations
                )

    declaration_results = tuple(
        _DeclarationResult(
            external=work.external,
            state=work.state,
            reason=work.reason,
            detail=work.detail,
            failed_module=work.failed_module,
            matched_candidate=work.matched_candidate,
            validation_basis=work.validation_basis,
            evidence=work.evidence,
            loaded_modules=work.loaded_modules,
        )
        for work in declaration_work
    )
    candidate_results = tuple(
        _CandidateResult(
            external=candidate,
            classification=candidate_classifications[index],
            matched=index in matched_candidates,
        )
        for index, candidate in enumerate(candidates)
    )
    return _PackageResult(package, declaration_results, candidate_results)


def _prefix_only(external):
    return external.prefix is not None and not external.modules


def _module_only(external):
    return external.prefix is None and bool(external.modules)


def _hybrid_external(external):
    return external.prefix is not None and bool(external.modules)


def _validator_outcome(detection, invalid_observations, conflict_details=()):
    if detection is None:
        if conflict_details:
            return "REVIEW_REQUIRED", "; ".join(sorted(set(conflict_details)))
        return None, None
    outcome = detection.get("outcome")
    if outcome == "success" and invalid_observations:
        return "UNSUPPORTED_DETECTION", "Spack returned an unsupported detection"
    if outcome == "success" and conflict_details:
        return "REVIEW_REQUIRED", "; ".join(sorted(set(conflict_details)))
    if outcome == "success":
        return "SUCCESS", None
    if outcome == "no_applicable_validator":
        return "NO_APPLICABLE_VALIDATOR", None
    return "VALIDATOR_FAILED", detection.get("detail")


def _validate_declared_external(
    package,
    index,
    declaration,
    broad_validation,
    targeted_results,
    module_results,
):
    """Dispatch one declaration to the validator for its locator shape."""

    if declaration.invalid_detail is not None:
        return _DeclarationResult(
            declaration,
            "REVIEW_REQUIRED",
            reason=_invalid_declaration_reason(declaration),
        )
    if _prefix_only(declaration):
        if broad_validation is not None:
            return broad_validation
        targeted_detection = targeted_results.get(package)
        if targeted_detection is None:
            return _DeclarationResult(
                declaration,
                "REVIEW_REQUIRED",
                reason="VALIDATOR_FAILED",
            )
        return _validate_prefix_external(declaration, targeted_detection)

    module_result = module_results.get(
        (package, index),
        {
            "outcome": "validator_failed",
            "loaded_modules": [],
        },
    )
    if _module_only(declaration):
        return _validate_module_external(declaration, module_result)
    if _hybrid_external(declaration):
        return _validate_hybrid_external(declaration, module_result)
    return _DeclarationResult(
        declaration,
        "REVIEW_REQUIRED",
        reason="INVALID_DECLARATION",
    )


def _reconcile_system_externals(system):
    """Validate and reconcile the fully concretized external set by package."""

    declarations = _canonicalize_declared_externals(_extract_system_externals(system))
    declarations_by_package = {}
    for declaration in declarations:
        declarations_by_package.setdefault(declaration.package, []).append(declaration)

    broad_requests = []
    for package in sorted(declarations_by_package):
        package_declarations = declarations_by_package[package]
        usable = [
            external
            for external in package_declarations
            if external.invalid_detail is None
        ]
        if not usable:
            continue
        broad_requests.append(
            {
                "id": package,
                "package": package,
                "initial_guess": None,
                "declared_specs": [external.spec for external in usable],
            }
        )
    broad_results = _run_spack_batch(broad_requests)

    broad_observations = {
        package: _spack_observations(
            package, detection, "broad_spack_detection"
        )
        for package, detection in broad_results.items()
    }

    broad_validations = {}
    unresolved_by_package = {}
    for package in sorted(declarations_by_package):
        detection = broad_results.get(package)
        observations = broad_observations.get(package, ())
        for index, declaration in enumerate(declarations_by_package[package]):
            if declaration.invalid_detail is not None or not _prefix_only(declaration):
                continue
            broad_validation = (
                _validate_broad_prefix_external(
                    declaration, detection, observations
                )
                if detection is not None
                else None
            )
            if broad_validation is not None:
                broad_validations[(package, index)] = broad_validation
                continue
            unresolved_by_package.setdefault(package, []).append(
                (index, declaration)
            )

    targeted_requests = []
    for package in sorted(unresolved_by_package):
        prefixes = []
        declared_specs = []
        for _, declaration in unresolved_by_package[package]:
            if declaration.prefix not in prefixes:
                prefixes.append(declaration.prefix)
            if declaration.spec not in declared_specs:
                declared_specs.append(declaration.spec)
        targeted_requests.append(
            {
                "id": package,
                "package": package,
                "initial_guess": prefixes,
                "declared_specs": declared_specs,
            }
        )

    targeted_results = {}
    if targeted_requests:
        try:
            targeted_results = _run_spack_batch(targeted_requests)
        except _SpackHelperError as error:
            failed_detection = _failed_spack_detection(str(error))
            targeted_results = {
                request["id"]: failed_detection for request in targeted_requests
            }

    module_validations = []
    for package, package_declarations in declarations_by_package.items():
        for index, declaration in enumerate(package_declarations):
            if declaration.invalid_detail is not None or not declaration.modules:
                continue
            hybrid_request = None
            if _hybrid_external(declaration):
                hybrid_request = {
                    "action": "detect",
                    "package": package,
                    "initial_guess": [declaration.prefix],
                    "declared_specs": [declaration.spec],
                }
            module_validations.append(
                ((package, index), declaration.modules, hybrid_request)
            )
    module_results = _run_module_validations(module_validations)
    _require_lmod_when_globally_unavailable(module_validations, module_results)

    package_results = []
    for package in sorted(declarations_by_package):
        package_declarations = declarations_by_package[package]
        validations = [
            _validate_declared_external(
                package,
                index,
                declaration,
                broad_validations.get((package, index)),
                targeted_results,
                module_results,
            )
            for index, declaration in enumerate(package_declarations)
        ]

        broad = broad_results.get(package)
        package_observations = broad_observations.get(package, ())
        candidates = tuple(
            external
            for external in package_observations
            if external.invalid_detail is None
        )
        candidates = _merge_validation_provenance(candidates, validations)
        invalid_observations = tuple(
            external
            for external in package_observations
            if external.invalid_detail is not None
        )
        conflict_details = [
            external.observation_conflict
            for external in candidates
            if external.observation_conflict
        ]
        conflict_details.extend(
            evidence.observation_conflict
            for validation in validations
            for evidence in validation.evidence
            if evidence.observation_conflict
        )
        result = _reconcile_package(
            package,
            package_declarations,
            candidates,
            validation_results=validations,
        )
        if invalid_observations:
            result = replace(
                result,
                candidates=result.candidates
                + tuple(
                    _CandidateResult(external=external)
                    for external in invalid_observations
                ),
            )
        outcome, detail = _validator_outcome(
            broad, invalid_observations, conflict_details
        )
        package_results.append(
            replace(result, validator_outcome=outcome, validator_detail=detail)
        )

    return tuple(package_results)


def _source_literal(spec, prefix):
    if not isinstance(spec, str) or not isinstance(prefix, str):
        return None
    if not spec or not prefix or any(char in spec + prefix for char in '"\\\r\n'):
        return None
    return f'{{"spec": "{spec}", "prefix": "{prefix}"}}'


def _declared_literal_external(external):
    if (
        external.invalid_detail is not None
        or not _prefix_only(external)
        or external.extra_attributes
    ):
        return None
    return _source_literal(external.raw_spec, external.raw_prefix)


def _detected_literal_external(external):
    if (
        external.invalid_detail is not None
        or not _prefix_only(external)
        or external.extra_attributes
    ):
        return None
    return _source_literal(external.spec, external.raw_prefix or external.prefix)


def _not_found_marker_source(source, declaration, *, add):
    """Add or remove only an exact machine-owned marker above one literal."""

    literal = _declared_literal_external(declaration)
    if literal is None:
        return None, "declaration is not a supported direct prefix-only literal"
    if source.count(literal) != 1:
        return None, "literal preimage does not occur exactly once"

    literal_start = source.index(literal)
    line_start = source.rfind("\n", 0, literal_start) + 1
    line_end = source.find("\n", literal_start)
    if line_end == -1:
        line_end = len(source)
    else:
        line_end += 1
    line = source[line_start:line_end]
    line_without_newline = line.rstrip("\r\n")
    if line_without_newline.strip() not in {literal, literal + ","}:
        return None, "literal is not on a standalone source line"
    indentation = line_without_newline[
        : len(line_without_newline) - len(line_without_newline.lstrip())
    ]
    marker_line = indentation + _NOT_FOUND_MARKER

    previous_start = source.rfind("\n", 0, max(line_start - 1, 0)) + 1
    previous_line = source[previous_start:line_start].rstrip("\r\n")
    marker_present = previous_line == marker_line
    if add:
        if marker_present:
            return source, None
        newline = "\r\n" if line.endswith("\r\n") else "\n"
        return source[:line_start] + marker_line + newline + source[line_start:], None
    if not marker_present:
        return source, None
    return source[:previous_start] + source[line_start:], None


def _replace_literal_external(source, declaration, candidate):
    """Replace one complete supported literal and clear its owned marker."""

    source, marker_reason = _not_found_marker_source(source, declaration, add=False)
    if source is None:
        return None, marker_reason
    old_literal = _declared_literal_external(declaration)
    new_literal = _detected_literal_external(candidate)
    if old_literal is None or new_literal is None:
        return None, "replacement is not a supported direct prefix-only literal"
    if source.count(old_literal) != 1:
        return None, "literal preimage does not occur exactly once"
    return source.replace(old_literal, new_literal, 1), None


def _supported_externals_lists(source, literal):
    lines = source.splitlines(keepends=True)
    open_re = re.compile(r'^(?P<indent>[ \t]*)"externals": \[\r?\n?$')
    close_re = re.compile(r'^(?P<indent>[ \t]*)\],?\r?\n?$')
    entry_re = re.compile(
        r'^(?P<indent>[ \t]*)\{"spec": "[^"\\\r\n]+", '
        r'"prefix": "[^"\\\r\n]+"\},\r?\n?$'
    )
    marker_re = re.compile(
        r'^(?P<indent>[ \t]*)# benchpark: external-status=not-found\r?\n?$'
    )

    matches = []
    for opening_index, opening_line in enumerate(lines):
        opening = open_re.match(opening_line)
        if not opening:
            continue
        closing_index = None
        for index in range(opening_index + 1, len(lines)):
            closing = close_re.match(lines[index])
            if closing and closing.group("indent") == opening.group("indent"):
                closing_index = index
                break
        if closing_index is None:
            continue

        entry_indent = None
        entry_lines = []
        valid = True
        for index in range(opening_index + 1, closing_index):
            entry = entry_re.match(lines[index])
            marker = marker_re.match(lines[index])
            if entry:
                if entry_indent is None:
                    entry_indent = entry.group("indent")
                elif entry.group("indent") != entry_indent:
                    valid = False
                    break
                entry_lines.append(index)
                continue
            if marker:
                following_entry = (
                    entry_re.match(lines[index + 1])
                    if index + 1 < closing_index
                    else None
                )
                if following_entry is None:
                    valid = False
                    break
                if marker.group("indent") != following_entry.group("indent"):
                    valid = False
                    break
                if entry_indent is None:
                    entry_indent = following_entry.group("indent")
                elif marker.group("indent") != entry_indent:
                    valid = False
                    break
                continue
            valid = False
            break
        if not valid or not entry_lines:
            continue

        literal_lines = [
            index
            for index in entry_lines
            if lines[index].rstrip("\r\n").strip() == literal + ","
        ]
        if len(literal_lines) != 1:
            continue
        list_preimage = "".join(lines[opening_index : closing_index + 1])
        if source.count(list_preimage) != 1:
            continue
        matches.append((closing_index, entry_indent, lines))
    return matches


def _add_literal_external(source, declaration, candidate):
    """Append one detected literal to a strictly supported multiline list."""

    old_literal = _declared_literal_external(declaration)
    new_literal = _detected_literal_external(candidate)
    if old_literal is None or new_literal is None:
        return None, "addition is not a supported direct prefix-only literal"
    if source.count(old_literal) != 1:
        return None, "literal preimage does not occur exactly once"
    matches = _supported_externals_lists(source, old_literal)
    if len(matches) != 1:
        return None, "no supported multiline externals list contains the literal"
    closing_index, entry_indent, lines = matches[0]
    newline = "\r\n" if lines[closing_index].endswith("\r\n") else "\n"
    lines.insert(closing_index, entry_indent + new_literal + "," + newline)
    return "".join(lines), None


def _system_source_path(system_spec):
    """Return the canonical source definition for a resolved SystemSpec."""

    system_repositories = benchpark.repo.paths[benchpark.repo.ObjectTypes.systems]
    return Path(system_repositories.filename_for_object_name(system_spec.name))


def _read_system_source(system_spec):
    """Read canonical source once, preserving the byte snapshot for apply."""

    source_path = _system_source_path(system_spec)
    try:
        source_bytes = source_path.read_bytes()
        return source_path, source_bytes, source_bytes.decode("utf-8"), None
    except (OSError, UnicodeDecodeError) as error:
        return source_path, None, None, str(error)


def _source_external_identity(external):
    """Identity used only to compare source behavior across cluster variants."""

    return (
        external.package,
        external.raw_spec,
        external.prefix,
        external.modules,
        external.extra_attributes,
    )


def _system_spec_with_cluster(system_spec, cluster):
    """Rebuild one concrete spec with all non-cluster selections unchanged."""

    parts = [system_spec.name]
    for name in sorted(system_spec.variants):
        values = (cluster,) if name == "cluster" else system_spec.variants[name]
        parts.append(benchpark.spec.VariantMap.stringify(name, values))
    return benchpark.spec.SystemSpec(" ".join(parts)).concretize()


def _cluster_scope(system_spec, declaration):
    """Prove that a source-controlled external is unique to one cluster."""

    if "cluster" not in system_spec.variants:
        return True, None

    selected = system_spec.variants["cluster"]
    if len(selected) != 1:
        return False, "cluster scope cannot be proven for a multi-valued cluster"

    applicable = []
    for condition, variants in system_spec.system_class.variants.items():
        cluster_variant = variants.get("cluster")
        if cluster_variant is not None and system_spec.satisfies(condition):
            applicable.append(cluster_variant)
    if not applicable:
        return False, "cluster scope cannot be proven from the system definition"
    if any(variant.values is None for variant in applicable):
        return False, "cluster scope cannot be proven from non-enumerable values"

    value_sets = {tuple(variant.values) for variant in applicable}
    if len(value_sets) != 1:
        return False, "cluster scope cannot be proven from multiple cluster definitions"
    clusters = next(iter(value_sets))
    siblings = [cluster for cluster in clusters if cluster != selected[0]]
    if not siblings:
        return True, None

    identity = _source_external_identity(declaration)
    for sibling in siblings:
        try:
            sibling_spec = _system_spec_with_cluster(system_spec, sibling)
            sibling_externals = _extract_system_externals(sibling_spec.system)
        except Exception as error:
            return (
                False,
                f"cluster scope cannot be proven because cluster={sibling} "
                f"could not resolve: {error}",
            )
        if any(
            _source_external_identity(external) == identity
            for external in sibling_externals
        ):
            return (
                False,
                f"external is also produced by cluster={sibling}",
            )
    return True, None


def _proposal_direct_source_reason(system_spec, declaration, scope_cache):
    if declaration is None:
        return "proposal has no direct source declaration"
    if _declared_literal_external(declaration) is None:
        return "declaration is not a supported direct prefix-only literal"

    identity = _source_external_identity(declaration)
    if identity not in scope_cache:
        scope_cache[identity] = _cluster_scope(system_spec, declaration)
    scoped, reason = scope_cache[identity]
    if not scoped:
        return reason
    return None


def _logical_proposals(package_result):
    proposals = []
    for declaration in package_result.declarations:
        if declaration.state == "REPLACEMENT":
            proposals.append(
                _Proposal(
                    "REPLACEMENT",
                    declaration.external,
                    declaration.matched_candidate,
                )
            )
        elif declaration.state == "NOT_FOUND":
            proposals.append(_Proposal("MARK_NOT_FOUND", declaration.external))
    for candidate in package_result.candidates:
        if candidate.classification == "ADDITIONAL_VERSION":
            proposals.append(_Proposal("ADDITIONAL_VERSION", None, candidate.external))
    return proposals


def _source_mutability_for_addition(
    system_spec, package_result, proposal, source, scope_cache
):
    if package_result.validator_outcome != "SUCCESS":
        return replace(
            proposal,
            source_reason="package candidate validation is incomplete",
        )
    if any(
        declaration.state == "REVIEW_REQUIRED"
        for declaration in package_result.declarations
    ):
        return replace(proposal, source_reason="package has unresolved declarations")
    candidate_literal = _detected_literal_external(proposal.candidate)
    if candidate_literal is None:
        return replace(
            proposal,
            source_reason="detected external is not a supported prefix-only literal",
        )
    if source.count(candidate_literal):
        return replace(
            proposal,
            source_reason="detected literal already occurs in source",
        )

    writable = []
    reasons = []
    for declaration_result in package_result.declarations:
        if declaration_result.state != "VALID":
            continue
        declaration = declaration_result.external
        reason = _proposal_direct_source_reason(
            system_spec, declaration, scope_cache
        )
        if reason is not None:
            reasons.append(reason)
            continue
        rewritten, reason = _add_literal_external(
            source, declaration, proposal.candidate
        )
        if rewritten is None:
            reasons.append(reason)
            continue
        writable.append(declaration)

    if len(writable) == 1:
        return replace(proposal, declaration=writable[0], source_mutable=True)
    if len(writable) > 1:
        return replace(
            proposal,
            source_reason="more than one supported insertion location was found",
        )
    return replace(
        proposal,
        source_reason=reasons[0]
        if reasons
        else "no supported existing externals list was found",
    )


def _source_mutability(system_spec, package_result, proposal, source, scope_cache):
    """Mark a logical proposal writable only when its exact source edit is safe."""

    if source is None:
        return replace(proposal, source_reason="canonical system source is unavailable")
    if proposal.action == "ADDITIONAL_VERSION":
        return _source_mutability_for_addition(
            system_spec, package_result, proposal, source, scope_cache
        )

    if (
        proposal.action == "REPLACEMENT"
        and package_result.validator_outcome != "SUCCESS"
    ):
        return replace(
            proposal,
            source_reason="package candidate validation is incomplete",
        )
    reason = _proposal_direct_source_reason(
        system_spec, proposal.declaration, scope_cache
    )
    if reason is not None:
        return replace(proposal, source_reason=reason)

    rewritten, reason = _proposal_source_edit(source, proposal)
    if rewritten is None:
        return replace(proposal, source_reason=reason)
    if rewritten == source:
        return replace(proposal, source_reason="source already has the requested state")
    return replace(proposal, source_mutable=True)


def _with_source_proposals(system_spec, package_results, source):
    """Attach logical proposals and their conservative source eligibility."""

    scope_cache = {}
    proposed_results = []
    for package_result in package_results:
        proposals = _logical_proposals(package_result)
        if source is not None:
            for declaration in package_result.declarations:
                if declaration.state != "VALID":
                    continue
                cleared, reason = _not_found_marker_source(
                    source, declaration.external, add=False
                )
                if cleared is not None and cleared != source:
                    proposals.append(
                        _Proposal("CLEAR_NOT_FOUND_MARKER", declaration.external)
                    )

        proposals = tuple(
            _source_mutability(
                system_spec, package_result, proposal, source, scope_cache
            )
            for proposal in proposals
        )
        proposed_results.append(replace(package_result, proposals=proposals))
    return tuple(proposed_results)


def _semantic_external_key(external):
    """Preserve malformed declarations too when checking a source semantic delta."""

    return (
        external.package,
        external.spec if external.spec is not None else external.raw_spec,
        external.prefix,
        external.modules,
        external.invalid_detail,
        external.unrepresentable,
    )


def _external_counter(externals):
    return Counter(_semantic_external_key(external) for external in externals)


def _all_declarations(package_results):
    return tuple(
        declaration.external
        for package_result in package_results
        for declaration in package_result.declarations
    )


def _proposal_source_edit(source, proposal):
    if proposal.action == "REPLACEMENT":
        return _replace_literal_external(
            source, proposal.declaration, proposal.candidate
        )
    if proposal.action == "ADDITIONAL_VERSION":
        return _add_literal_external(source, proposal.declaration, proposal.candidate)
    if proposal.action == "MARK_NOT_FOUND":
        return _not_found_marker_source(source, proposal.declaration, add=True)
    if proposal.action == "CLEAR_NOT_FOUND_MARKER":
        return _not_found_marker_source(source, proposal.declaration, add=False)
    return None, "unsupported source mutation"


def _strip_not_found_markers(source):
    marker = re.compile(
        r"^[ \t]*# benchpark: external-status=not-found(?:\r?\n|$)"
    )
    return "".join(
        line for line in source.splitlines(keepends=True) if not marker.match(line)
    )


def _verify_marker_text(source, rewritten, proposals):
    """Confirm marker-only edits did not alter any other source text."""

    non_marker_source = source
    for proposal in proposals:
        if proposal.action in {"MARK_NOT_FOUND", "CLEAR_NOT_FOUND_MARKER"}:
            continue
        non_marker_source, reason = _proposal_source_edit(non_marker_source, proposal)
        if non_marker_source is None:
            raise _ApplyVerificationError(reason)
    if _strip_not_found_markers(rewritten) != _strip_not_found_markers(
        non_marker_source
    ):
        raise _ApplyVerificationError(
            "machine-owned marker edits changed unrelated source text"
        )


@contextmanager
def _candidate_system_spec(system_spec, source_path, source):
    """Resolve a candidate source file through a temporary system repository."""

    system_repositories = benchpark.repo.paths[benchpark.repo.ObjectTypes.systems]
    repository = system_repositories.repo_for_obj(system_spec.name)
    repository_root = Path(repository.root).resolve()
    try:
        relative_directory = source_path.parent.resolve().relative_to(repository_root)
    except ValueError as error:
        raise _ApplyVerificationError(
            "canonical system source is outside its repository"
        ) from error

    with tempfile.TemporaryDirectory(
        prefix="benchpark-system-external-"
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        shutil.copy2(
            repository.config_file,
            temporary_root / Path(repository.config_file).name,
        )
        temporary_system_directory = temporary_root / relative_directory
        shutil.copytree(
            source_path.parent,
            temporary_system_directory,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        (temporary_system_directory / source_path.name).write_bytes(
            source.encode("utf-8")
        )

        old_sys_repo = benchpark.spec.sys_repo
        old_dont_write_bytecode = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            with benchpark.repo.override_ramble_hardcoded_globals():
                with benchpark.repo.use_repositories(
                    str(temporary_root),
                    *system_repositories.repos,
                    object_type=benchpark.repo.ObjectTypes.systems,
                ) as candidate_repositories:
                    benchpark.spec.sys_repo = candidate_repositories
                    yield benchpark.spec.SystemSpec(str(system_spec)).concretize()
        finally:
            benchpark.spec.sys_repo = old_sys_repo
            sys.dont_write_bytecode = old_dont_write_bytecode


def _expected_external_delta(package_results, proposals):
    expected = _external_counter(_all_declarations(package_results))
    for proposal in proposals:
        if proposal.action == "REPLACEMENT":
            declaration_key = _semantic_external_key(proposal.declaration)
            if expected[declaration_key] < 1:
                raise _ApplyVerificationError(
                    "logical replacement is absent from the original external set"
                )
            expected[declaration_key] -= 1
            expected[_semantic_external_key(proposal.candidate)] += 1
        elif proposal.action == "ADDITIONAL_VERSION":
            expected[_semantic_external_key(proposal.candidate)] += 1
    return +expected


def _frozen_validation_results(new_declarations, package_result):
    """Reuse only frozen validation evidence after a verified source edit."""

    old_results = list(package_result.declarations)
    candidates = tuple(
        candidate.external
        for candidate in package_result.candidates
        if candidate.external.invalid_detail is None
    )
    validations = []
    for declaration in new_declarations:
        old_index = next(
            (
                index
                for index, old_result in enumerate(old_results)
                if _semantic_external_key(old_result.external)
                == _semantic_external_key(declaration)
            ),
            None,
        )
        if old_index is not None:
            old_result = old_results.pop(old_index)
            validations.append(replace(old_result, external=declaration))
            continue
        matching_candidate = next(
            (
                candidate
                for candidate in candidates
                if _identity_key(candidate) == _identity_key(declaration)
            ),
            None,
        )
        if (
            matching_candidate is not None
            and package_result.validator_outcome == "SUCCESS"
        ):
            validations.append(
                _DeclarationResult(
                    declaration,
                    "VALID",
                    validation_basis="frozen_broad_spack_detection",
                    evidence=(matching_candidate,),
                )
            )
            continue
        validations.append(
            _DeclarationResult(
                declaration,
                "REVIEW_REQUIRED",
                reason="FROZEN_EVIDENCE_MISMATCH",
            )
        )
    return validations, candidates


def _reconcile_frozen_evidence(package_results, declarations):
    """Reconcile edited declarations without collecting new environmental evidence."""

    by_package = {}
    for declaration in declarations:
        by_package.setdefault(declaration.package, []).append(declaration)
    prior_by_package = {result.package: result for result in package_results}
    if set(by_package) != set(prior_by_package):
        raise _ApplyVerificationError(
            "edited system changed the set of external package declarations"
        )

    reconciled = []
    for package in sorted(by_package):
        prior = prior_by_package[package]
        validations, candidates = _frozen_validation_results(by_package[package], prior)
        result = _reconcile_package(
            package,
            by_package[package],
            candidates,
            validation_results=validations,
        )
        invalid_candidates = tuple(
            candidate
            for candidate in prior.candidates
            if candidate.external.invalid_detail is not None
        )
        if invalid_candidates:
            result = replace(result, candidates=result.candidates + invalid_candidates)
        reconciled.append(
            replace(
                result,
                validator_outcome=prior.validator_outcome,
                validator_detail=prior.validator_detail,
            )
        )
    return tuple(reconciled)


def _atomic_replace_source(source_path, original_bytes, rewritten_source):
    """Replace one source file atomically after a last unchanged-byte check."""

    try:
        mode = stat.S_IMODE(source_path.stat().st_mode)
        if source_path.read_bytes() != original_bytes:
            raise _ApplyVerificationError(
                "canonical system source changed during the apply transaction"
            )
        descriptor, temporary_path = tempfile.mkstemp(
            prefix=source_path.name + ".", dir=str(source_path.parent)
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(rewritten_source.encode("utf-8"))
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary_path, mode)
            if source_path.read_bytes() != original_bytes:
                raise _ApplyVerificationError(
                    "canonical system source changed during the apply transaction"
                )
            os.replace(temporary_path, source_path)
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)
    except OSError as error:
        raise _ApplyVerificationError(str(error)) from error


def _apply_source_proposals(
    system_spec, package_results, source_path, source_bytes, source
):
    """Apply every eligible edit as one verified, atomic transaction."""

    proposals = tuple(
        proposal
        for package_result in package_results
        for proposal in package_result.proposals
        if proposal.source_mutable
    )
    if not proposals:
        return package_results, False

    rewritten = source
    for proposal in proposals:
        rewritten, reason = _proposal_source_edit(rewritten, proposal)
        if rewritten is None:
            raise _ApplyVerificationError(reason)
    try:
        compile(rewritten, str(source_path), "exec")
    except SyntaxError as error:
        raise _ApplyVerificationError(f"candidate source has invalid syntax: {error}")
    _verify_marker_text(source, rewritten, proposals)

    try:
        with _candidate_system_spec(
            system_spec, source_path, rewritten
        ) as candidate_spec:
            candidate_declarations = _canonicalize_declared_externals(
                _extract_system_externals(candidate_spec.system)
            )
    except _ApplyVerificationError:
        raise
    except Exception as error:
        raise _ApplyVerificationError(
            f"candidate system could not resolve: {error}"
        ) from error

    expected = _expected_external_delta(package_results, proposals)
    actual = _external_counter(candidate_declarations)
    if actual != expected:
        raise _ApplyVerificationError(
            "candidate system external delta does not match the logical proposal"
        )
    reconciled = _reconcile_frozen_evidence(package_results, candidate_declarations)
    _atomic_replace_source(source_path, source_bytes, rewritten)
    return reconciled, True


def _external_text(external):
    spec = external.spec or external.raw_spec or "<unrepresentable spec>"
    fields = [f"{external.package} {spec}"]
    if external.prefix is not None:
        fields.append(f"prefix={external.prefix}")
    if external.modules:
        fields.append("modules=" + ", ".join(external.modules))
    if external.invalid_detail:
        fields.append(f"detail={external.invalid_detail}")
    if external.observation_conflict:
        fields.append(f"observation conflict={external.observation_conflict}")
    return " | ".join(fields)


def _report_reconciliation(system_spec, package_results, *, heading=None):
    """Render the private result in a concise human-readable form."""

    print(heading or f"External reconciliation for {system_spec}")
    for package_result in package_results:
        validator = package_result.validator_outcome or "NOT_REQUIRED"
        validator_detail = (
            f": {package_result.validator_detail}"
            if package_result.validator_detail
            else ""
        )
        print(
            f"\n{package_result.package} "
            f"(broad Spack detection: {validator}{validator_detail})"
        )
        for declaration in package_result.declarations:
            suffix = f" [{declaration.reason}]" if declaration.reason else ""
            basis = (
                f"; basis={declaration.validation_basis}"
                if declaration.validation_basis
                else ""
            )
            print(
                f"  {declaration.state}{suffix}: "
                f"{_external_text(declaration.external)}{basis}"
            )
            if declaration.failed_module:
                print("    failed module: " + declaration.failed_module)
            if declaration.detail:
                print("    detail: " + declaration.detail)
            if declaration.loaded_modules:
                print("    loaded modules: " + ", ".join(declaration.loaded_modules))
                automatic_modules = [
                    module
                    for module in declaration.loaded_modules
                    if module not in declaration.external.modules
                ]
                if automatic_modules:
                    print(
                        "    automatically loaded modules: "
                        + ", ".join(automatic_modules)
                    )
            for evidence in declaration.evidence:
                print("    evidence: " + _external_text(evidence))
        for candidate in package_result.candidates:
            if candidate.matched:
                label = "MATCHED"
            elif candidate.classification:
                label = candidate.classification
            else:
                label = "OBSERVED"
            provenance = (
                "; observed by=" + ", ".join(candidate.external.observed_by)
                if candidate.external.observed_by
                else ""
            )
            print(f"  {label}: {_external_text(candidate.external)}{provenance}")
        for proposal in package_result.proposals:
            candidate = (
                " -> " + _external_text(proposal.candidate)
                if proposal.candidate is not None
                else ""
            )
            writable = "writable" if proposal.source_mutable else "report-only"
            reason = f" ({proposal.source_reason})" if proposal.source_reason else ""
            target = (
                _external_text(proposal.declaration)
                if proposal.declaration
                else package_result.package
            )
            print(
                f"  proposal {proposal.action} [{writable}]: "
                f"{target}{candidate}{reason}"
            )


def _reconciliation_exit_status(package_results):
    """Return the stable v1 result status, not an operational-error status."""

    for package_result in package_results:
        if package_result.validator_outcome in {
            "VALIDATOR_FAILED",
            "UNSUPPORTED_DETECTION",
            "REVIEW_REQUIRED",
        }:
            return 1
        if any(
            declaration.state
            in {"NOT_FOUND", "REPLACEMENT", "REVIEW_REQUIRED"}
            for declaration in package_result.declarations
        ):
            return 1
        if any(
            candidate.classification == "ADDITIONAL_VERSION"
            for candidate in package_result.candidates
        ):
            return 1
    return 0


def run(args):
    try:
        system_spec = benchpark.spec.SystemSpec(" ".join(args.spec)).concretize()
        package_results = _reconcile_system_externals(system_spec.system)
    except Exception as error:
        print(
            "External reconciliation could not produce a trustworthy result: "
            f"{error}"
        )
        return 2

    propose = getattr(args, "propose", False)
    apply = getattr(args, "apply", False)
    source_path = source_bytes = source = source_error = None
    if propose or apply:
        source_path, source_bytes, source, source_error = _read_system_source(
            system_spec
        )
        package_results = _with_source_proposals(system_spec, package_results, source)
        if source_error:
            print(f"Source mutation is unavailable: {source_error}")

    _report_reconciliation(system_spec, package_results)

    if not apply:
        return _reconciliation_exit_status(package_results)
    if source_error:
        return _reconciliation_exit_status(package_results)

    try:
        package_results, applied = _apply_source_proposals(
            system_spec, package_results, source_path, source_bytes, source
        )
    except _ApplyVerificationError as error:
        print(f"External reconciliation apply failed: {error}")
        return 2
    if applied:
        _report_reconciliation(
            system_spec, package_results, heading="Post-apply external reconciliation"
        )
    else:
        print("No eligible source changes were applied.")
    return _reconciliation_exit_status(package_results)
