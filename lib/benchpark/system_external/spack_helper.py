# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

"""Spack-side detection helper for ``benchpark system external``.

This script is deliberately compatible with the Python used by ``spack python``.
It only parses, canonicalizes, and invokes Spack's existing raw finders.
"""

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
    return [(item, spack.spec.parse_with_version_concrete(item)) for item in specs]


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
        repository = spack.util.lang.ensure_unwrapped(spack.repo.PATH)
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
