# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import ramble.repository

from benchpark.paths import paths


def test_compiler_attribution_declares_feature_modes():
    repo = ramble.repository.Repo(
        str(paths.benchpark_root / "modifiers"),
        object_type=ramble.repository.ObjectTypes.modifiers,
    )
    modifier_class = repo.get_obj_class("compiler-attribution")

    plugin_specs = modifier_class.software_specs["compiler_attribution_plugin"]

    assert len(plugin_specs) == 1
    assert plugin_specs[0].pkg_spec == "compiler-attribution-plugin"
    assert {
        "association",
        "remark_counts",
        "remark_details",
        "kru",
        "ir_metrics",
        "per_pass_ir_metrics",
    }.issubset(modifier_class.modes)


def test_compiler_attribution_adds_postprocessing_command():
    repo = ramble.repository.Repo(
        str(paths.benchpark_root / "modifiers"),
        object_type=ramble.repository.ObjectTypes.modifiers,
    )
    modifier = repo.get("compiler-attribution")
    modifier.set_usage_mode("association")

    pre_exec, post_exec = modifier.compiler_attribution("run", None)

    assert len(pre_exec) == 1
    assert len(post_exec) == 1
    assert post_exec[0].name == "postprocess-compiler-attribution-run"
    assert post_exec[0].template == [
        "python3 "
        "\"$(spack -e '{env_path}' location -i "
        'compiler-attribution-plugin)/bin/compiler-attribution-postprocess" '
        "'{env_path}/compiler-attribution/extraction_plugin_output' "
        "'{experiment_run_dir}/{experiment_name}.run.compiler_attribution.trace.jsonl' "
        "'{experiment_run_dir}/{experiment_name}.run.compiler_attribution.postprocessed.json'"
    ]


def test_compiler_attribution_skips_postprocessing_without_association():
    repo = ramble.repository.Repo(
        str(paths.benchpark_root / "modifiers"),
        object_type=ramble.repository.ObjectTypes.modifiers,
    )
    modifier = repo.get("compiler-attribution")
    modifier.set_usage_mode("kru")

    assert modifier.compiler_attribution("run", None) == ([], [])


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
