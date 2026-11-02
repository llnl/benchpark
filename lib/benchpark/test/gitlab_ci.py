# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Checks on the LC GitLab test matrices in .gitlab/tests/."""

import re

import pytest
import yaml

from benchpark.paths import paths

SHARED_SLURM_TESTS = paths.benchpark_root / ".gitlab/tests/shared_slurm_clusters.yml"

# Tests that pass under Slurm (nightly.yml) but fail in shared_slurm_clusters.yml,
# where they run inside a Flux instance started in a Slurm job. Each entry is
# (HOST, BENCHMARK, regex searched in VARIANT or None for any VARIANT, reason).
EXCLUDED_FROM_SHARED_SLURM_TESTS = [
    (
        "matrix",
        "branson",
        r"\+cuda($|[\s+~])",
        "it fails under Flux (CUDA error synchronizing after the source kernel) "
        "but passes under Slurm, so it is tested in nightly.yml instead",
    ),
]


class GitLabLoader(yaml.SafeLoader):
    """SafeLoader that also accepts GitLab's !reference tag."""


GitLabLoader.add_constructor(
    "!reference", lambda loader, node: loader.construct_sequence(node)
)


def as_list(value):
    return value if isinstance(value, list) else [value]


def matrix_combinations(path):
    """Yield (job, HOST, BENCHMARK, VARIANT) for every parallel:matrix job."""
    with open(path) as stream:
        config = yaml.load(stream, Loader=GitLabLoader)
    for job, body in config.items():
        parallel = body.get("parallel") if isinstance(body, dict) else None
        if not isinstance(parallel, dict):
            continue
        for entry in parallel.get("matrix", []):
            for host in as_list(entry.get("HOST")):
                for benchmark in as_list(entry.get("BENCHMARK")):
                    for variant in as_list(entry.get("VARIANT")):
                        yield job, host, benchmark, variant or ""


@pytest.mark.parametrize(
    "host,benchmark,variant_regex,reason",
    EXCLUDED_FROM_SHARED_SLURM_TESTS,
    ids=[
        f"{host}-{benchmark}"
        for host, benchmark, *_ in EXCLUDED_FROM_SHARED_SLURM_TESTS
    ],
)
def test_shared_slurm_tests_exclusions(host, benchmark, variant_regex, reason):
    combinations = list(matrix_combinations(SHARED_SLURM_TESTS))

    # Make sure the check still sees this host, so it can't pass vacuously
    assert any(h == host for _, h, _, _ in combinations), (
        f"No HOST={host} jobs found in {SHARED_SLURM_TESTS.name}; update this test"
    )

    found = [
        f"{job}: [{h}, {b}, {v}]"
        for job, h, b, v in combinations
        if h == host
        and b == benchmark
        and (variant_regex is None or re.search(variant_regex, v))
    ]
    assert not found, (
        f"Remove {benchmark} on {host} from {SHARED_SLURM_TESTS.name}: {reason}. "
        f"Found: {'; '.join(found)}"
    )
