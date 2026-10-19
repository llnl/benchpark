# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import ramble.repository

from benchpark.paths import paths


def test_compiler_attribution_enables_association():
    repo = ramble.repository.Repo(
        str(paths.benchpark_root / "modifiers"),
        object_type=ramble.repository.ObjectTypes.modifiers,
    )
    modifier_class = repo.get_obj_class("compiler-attribution")

    plugin_specs = modifier_class.software_specs["compiler_attribution_plugin"]

    assert len(plugin_specs) == 1
    assert plugin_specs[0].pkg_spec == "compiler-attribution-plugin +association"


def test_compiler_attribution_adds_association_runtime_to_root_spec():
    repo = ramble.repository.Repo(
        str(paths.benchpark_root / "modifiers"),
        object_type=ramble.repository.ObjectTypes.modifiers,
    )
    modifier_class = repo.get_obj_class("compiler-attribution")

    instrumented_spec = modifier_class._instrumented_spec(
        "raja-perf@2025.12.1 +rocm",
        "/plugin",
        "compiler-attribution-plugin +association",
    )

    assert instrumented_spec == (
        "raja-perf@2025.12.1 +rocm "
        "ldflags='/plugin/lib/CaliperAssociationLib.so "
        "-Wl,-rpath,/plugin/lib -Wl,--export-dynamic'"
    )


def test_compiler_attribution_leaves_root_spec_without_association_unchanged():
    repo = ramble.repository.Repo(
        str(paths.benchpark_root / "modifiers"),
        object_type=ramble.repository.ObjectTypes.modifiers,
    )
    modifier_class = repo.get_obj_class("compiler-attribution")

    benchmark_spec = "raja-perf@2025.12.1 +rocm"
    assert (
        modifier_class._instrumented_spec(
            benchmark_spec,
            "/plugin",
            "compiler-attribution-plugin ~association",
        )
        == benchmark_spec
    )
