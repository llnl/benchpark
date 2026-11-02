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

# Tests known to fail in shared_slurm_clusters.yml, where they run inside a Flux
# instance started in a Slurm job. Each entry is (HOST, BENCHMARK, VARIANT specs,
# reason). A spec such as "+cuda" also matches a longer VARIANT like
# "+cuda~gpu-aware-mpi", and None matches a test with no VARIANT.
EXCLUDED_FROM_SHARED_SLURM_TESTS = [
    (
        "matrix",
        "branson",
        ["+cuda"],
        "it fails under Flux (CUDA error synchronizing after the source kernel) "
        "but passes under Slurm, so it is tested in nightly.yml instead",
    ),
    (
        "dane",
        "phloem",
        [None],
        "it fails during MPI_Finalize under Flux, so it is tested under Slurm "
        "in nightly.yml instead",
    ),
    (
        "matrix",
        "phloem",
        [None, "+cuda"],
        "it fails during MPI_Finalize under Flux",
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


def variant_matches(variant, spec):
    """Match an empty VARIANT (spec None) or one that contains spec, e.g. +cuda."""
    if spec is None:
        return not variant
    return re.search(re.escape(spec) + r"($|[\s+~])", variant) is not None


@pytest.mark.parametrize(
    "host,benchmark,variants,reason",
    EXCLUDED_FROM_SHARED_SLURM_TESTS,
    ids=[
        f"{host}-{benchmark}"
        for host, benchmark, *_ in EXCLUDED_FROM_SHARED_SLURM_TESTS
    ],
)
def test_shared_slurm_tests_exclusions(host, benchmark, variants, reason):
    combinations = list(matrix_combinations(SHARED_SLURM_TESTS))

    # Make sure the check still sees this host, so it can't pass vacuously
    assert any(h == host for _, h, _, _ in combinations), (
        f"No HOST={host} jobs found in {SHARED_SLURM_TESTS.name}; update this test"
    )

    found = [
        f"{job}: [{', '.join(filter(None, (h, b, v)))}]"
        for job, h, b, v in combinations
        if h == host
        and b == benchmark
        and any(variant_matches(v, spec) for spec in variants)
    ]
    assert not found, (
        f"Remove {benchmark} on {host} from {SHARED_SLURM_TESTS.name}: {reason}. "
        f"Found: {'; '.join(found)}"
    )
