# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import subprocess

import benchpark.paths


def test_list():
    for subcmd in ["experiments", "modifiers", "systems", "benchmarks"]:
        # Test with title (default behavior)
        result_with_title = subprocess.run(
            [benchpark.paths.benchpark_root / "bin/benchpark", "list", subcmd],
            check=True,
            capture_output=True,
            text=True,
        )
        assert (
            f"{subcmd.capitalize()}" in result_with_title.stdout
        ), f"Title missing for {subcmd} in output with title"

        # Test without title (--no-title flag)
        result_no_title = subprocess.run(
            [
                benchpark.paths.benchpark_root / "bin/benchpark",
                "list",
                subcmd,
                "--no-title",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert (
            f"{subcmd.capitalize()}:" not in result_no_title.stdout
        ), f"Title found for {subcmd} in output without title"

        if subcmd == "modifiers":
            assert (
                "amg2023" in result_with_title.stdout
                and "amg2023" in result_no_title.stdout
            )

    # Check filtering
    check_cuda = subprocess.run(
        [
            benchpark.paths.benchpark_root / "bin/benchpark",
            "list",
            "experiments",
            "--experiment",
            "cuda",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    # CUDA benchmark
    assert "amg2023" in check_cuda.stdout
    # Non CUDA benchmark
    assert "gpcnet" not in check_cuda.stdout


def test_tags():
    subprocess.run(
        [benchpark.paths.benchpark_root / "bin/benchpark", "tags", "-a", "ad"],
        check=True,
    )


def test_info():
    text = subprocess.run(
        [
            benchpark.paths.benchpark_root / "bin/benchpark",
            "list",
            "systems",
            "--no-title",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    result = [
        line.lstrip().split(" ")[0]
        for line in text.stdout.splitlines()
        if line.strip() and not line.lstrip().startswith("generic-x86")
    ]

    for r in result:
        subprocess.run(
            [benchpark.paths.benchpark_root / "bin/benchpark", "info", "system", r],
            check=True,
            capture_output=True,
        )
