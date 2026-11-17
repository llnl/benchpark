# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the compiler_attribution modifier's setup-phase instrumentation,
with Spack replaced by a recorder."""

import os
import subprocess
from types import SimpleNamespace

import pytest
import ramble.repository

from benchpark.paths import paths

PLUGIN_PREFIX = "/opt/compiler-attribution-plugin"
RENDERED = {"rendered": "packages"}


class FakePackage:
    def __init__(self, name, spec):
        self.name = name
        self._spec = spec

    def spec_str(self, all_packages=None, compiler=True):
        assert all_packages is RENDERED and compiler is False
        return self._spec


class FakeWorkspace:
    def __init__(self, packages, dry_run=False):
        self.dry_run = dry_run
        self.cache = set()
        self.rendered = []
        software_env = SimpleNamespace(name="saxpy", _packages=packages)

        def render_environment(env_name, expander, package_manager, require):
            assert require is True
            self.rendered.append(env_name)
            return software_env

        self.software_environments = SimpleNamespace(
            _rendered_packages=RENDERED, render_environment=render_environment
        )

    def check_cache(self, key):
        return key in self.cache

    def add_to_cache(self, key):
        self.cache.add(key)


def _app_inst(env_path, package_manager="spack", env_name="saxpy"):
    def expand_var_name(name):
        assert name == "env_name"
        if env_name is None:
            raise KeyError(name)
        return env_name

    created = []
    manager = None
    if package_manager is not None:
        manager = SimpleNamespace(
            name=package_manager,
            _software_create_env=lambda ws, app: created.append(app),
        )
    return SimpleNamespace(
        name="saxpy",
        package_manager=manager,
        created=created,
        expander=SimpleNamespace(
            env_path=str(env_path),
            application_spec="saxpy",
            expand_var_name=expand_var_name,
        ),
    )


@pytest.fixture
def modifier():
    repo = ramble.repository.Repo(
        str(paths.benchpark_root / "modifiers"),
        object_type=ramble.repository.ObjectTypes.modifiers,
    )
    return repo.get("compiler-attribution")


class SpackCalls(list):
    """Recorded (args, env) pairs, plus the answers the fake Spack gives."""


@pytest.fixture
def spack_calls(modifier, tmp_path):
    """Record the Spack commands the modifier runs and answer its queries."""
    calls = SpackCalls()
    state = {"prefix": PLUGIN_PREFIX + "\n", "build_stage": [str(tmp_path / "stage")]}

    def fake_run_spack(args, env=None, capture_output=False):
        calls.append((args, env))
        if args[2:4] == ["location", "-i"]:
            return SimpleNamespace(stdout=state["prefix"])
        if args[2:5] == ["config", "get", "config"]:
            stages = "".join(f"  - {stage}\n" for stage in state["build_stage"])
            return SimpleNamespace(stdout=f"config:\n  build_stage:\n{stages}")
        return SimpleNamespace(stdout="")

    modifier._run_spack = fake_run_spack
    calls.state = state
    return calls


PACKAGES = [
    FakePackage("saxpy", "saxpy@1.0 +openmp"),
    FakePackage(
        "compiler_attribution_plugin",
        "compiler-attribution-plugin@main +association+kru",
    ),
]


def test_instrument_benchmark_rebuilds_with_plugin(modifier, spack_calls, tmp_path):
    env_path = tmp_path / "software" / "saxpy"
    workspace = FakeWorkspace(PACKAGES)
    app_inst = _app_inst(env_path)
    spack_calls.state["build_stage"] = [
        "$tempdir/relative-stage",
        str(tmp_path / "stage"),
    ]

    modifier._instrument_benchmark(workspace, app_inst)

    lib = f"{PLUGIN_PREFIX}/lib"
    instrumented = (
        "saxpy@1.0 +openmp ldflags='"
        f"{lib}/CaliperAssociationLib.so -Wl,-rpath,{lib} -Wl,--export-dynamic'"
    )
    env = str(env_path)
    assert [args for args, _ in spack_calls] == [
        ["-e", env, "install", "compiler-attribution-plugin"],
        ["-e", env, "location", "-i", "compiler-attribution-plugin"],
        ["-e", env, "change", "--match-spec", "saxpy", instrumented],
        ["-e", env, "concretize", "--force"],
        ["-e", env, "install", "--only", "dependencies", instrumented],
        ["-e", env, "config", "get", "config"],
        [
            "-e",
            env,
            "install",
            "--yes-to-all",
            "--only",
            "package",
            "--overwrite",
            "--no-cache",
            "--dirty",
            instrumented,
        ],
    ]
    assert app_inst.created == [app_inst]
    assert set(workspace.rendered) == {"saxpy"}

    build_env = spack_calls[-1][1]
    flags = (
        f"-fpass-plugin={lib}/CompilerAttributionPlugin.so -mllvm -pass-remarks=.*"
        " -mllvm -pass-remarks-analysis=kernel-resource-usage"
    )
    for name in ("SPACK_CXXFLAGS", "CXXFLAGS", "HIPFLAGS"):
        assert build_env[name].endswith(flags)
    assert build_env["EXTRACTION_SRC_PATH"] == str(tmp_path)
    assert build_env["ASSOCIATION_SRC_PATH"] == str(tmp_path)
    assert build_env["EXTRACTION_OUT_PATH"] == str(env_path / "compiler-attribution")
    assert (env_path / "compiler-attribution").is_dir()
    assert build_env["EXTRACTION_KRU"] == "ON"
    assert build_env["EXTRACTION_REMARK_COUNTS"] == "OFF"
    assert build_env["EXTRACTION_PER_PASS_IR_METRICS"] == "OFF"

    # A second application sharing the environment is only instrumented once
    count = len(spack_calls)
    modifier._instrument_benchmark(workspace, app_inst)
    assert len(spack_calls) == count


def test_instrument_benchmark_without_association(modifier, spack_calls, tmp_path):
    # No plugin package in the environment: nothing to link, no respec
    workspace = FakeWorkspace([FakePackage("saxpy", "saxpy@1.0")])

    modifier._instrument_benchmark(workspace, _app_inst(tmp_path / "env"))

    commands = [args[2] for args, _ in spack_calls]
    assert "change" not in commands and "concretize" not in commands
    assert spack_calls[-1][0][-1] == "saxpy@1.0"
    assert spack_calls[-1][1]["EXTRACTION_KRU"] == "OFF"


def test_instrument_benchmark_dry_run_does_nothing(modifier, spack_calls):
    modifier._instrument_benchmark(FakeWorkspace(PACKAGES, dry_run=True), None)

    assert spack_calls == []


@pytest.mark.parametrize("package_manager", [None, "pip"])
def test_instrument_benchmark_requires_spack(modifier, spack_calls, package_manager):
    workspace = FakeWorkspace(PACKAGES)

    with pytest.raises(SystemExit):
        modifier._instrument_benchmark(workspace, None)
    with pytest.raises(SystemExit):
        modifier._instrument_benchmark(
            workspace, _app_inst("/env", package_manager=package_manager)
        )
    assert spack_calls == []


def test_instrument_benchmark_requires_plugin_prefix(modifier, spack_calls, tmp_path):
    spack_calls.state["prefix"] = "\n"

    with pytest.raises(SystemExit):
        modifier._instrument_benchmark(FakeWorkspace(PACKAGES), _app_inst(tmp_path))


def test_application_package_must_be_in_environment(modifier, tmp_path):
    workspace = FakeWorkspace([FakePackage("cmake", "cmake@3.27")])

    with pytest.raises(SystemExit):
        modifier._application_package(workspace, _app_inst(tmp_path))


def test_environment_name_falls_back_to_application(modifier, tmp_path):
    assert modifier._active_environment_name(_app_inst(tmp_path, env_name=None)) == (
        "saxpy"
    )


def test_first_absolute_build_stage(modifier, spack_calls):
    # Only ~ is expanded, so Spack's $tempdir-style paths do not qualify
    spack_calls.state["build_stage"] = ["$tempdir/stage", "relative/stage"]
    with pytest.raises(SystemExit):
        modifier._first_absolute_build_stage("/env")

    spack_calls.state["build_stage"] = ["$tempdir/stage", "~/stage"]
    assert modifier._first_absolute_build_stage("/env") == os.path.expanduser("~/stage")

    modifier._run_spack = lambda args, **kwargs: SimpleNamespace(
        stdout="build_stage: /scratch/stage\n"
    )
    assert modifier._first_absolute_build_stage("/env") == "/scratch/stage"


def test_run_spack(modifier, monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        if "fail" in cmd:
            raise subprocess.CalledProcessError(1, cmd)
        return SimpleNamespace(stdout="ok")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert modifier._run_spack(["find"], capture_output=True).stdout == "ok"
    assert calls[0] == (
        ["spack", "find"],
        {"check": True, "text": True, "env": None, "capture_output": True},
    )
    with pytest.raises(SystemExit):
        modifier._run_spack(["fail"])


def test_append_flag_ignores_empty_flags(modifier):
    env = {"CXXFLAGS": "-O2"}
    modifier._append_flag(env, "CXXFLAGS", "")
    modifier._append_flag(env, "CXXFLAGS", "-g")
    modifier._append_flag(env, "HIPFLAGS", "-g")

    assert env == {"CXXFLAGS": "-O2 -g", "HIPFLAGS": "-g"}
