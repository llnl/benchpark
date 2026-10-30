# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import hashlib
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import ramble.repository
from ramble.expander import Expander
from ramble.util.executable import CommandExecutable

import benchpark.spec
from benchpark.error import BenchparkError
from benchpark.paths import paths


@pytest.fixture
def modifier():
    repo = ramble.repository.Repo(
        str(paths.benchpark_root / "modifiers"),
        object_type=ramble.repository.ObjectTypes.modifiers,
    )
    obj = repo.get("compiler-memtrace")
    obj.set_usage_mode("trace")
    obj.expander = Expander(
        {
            "compiler_memtrace_executables": "run",
            "compiler_memtrace_addrspaces": "1:0",
            "compiler_memtrace_prevectorize": "0",
            "compiler_memtrace_waves_per_eu": "",
            "compiler_memtrace_timing": "0",
        },
        None,
    )
    obj._builds_file = "/builds/builds.json"
    obj._python = sys.executable
    return obj


@pytest.fixture
def app(tmp_path):
    return SimpleNamespace(
        expander=SimpleNamespace(env_path=str(tmp_path), workload_name="suite"),
        get_workload=lambda name: SimpleNamespace(executables=["run"]),
    )


@pytest.fixture
def metadata_environment(tmp_path, monkeypatch):
    # Persist real Spec DAGs and activate their environment through Spack's CLI.
    # This tests environment APIs, compiler virtual edges, and package accessors
    # without installing a compiler or running the solver.
    env_path = tmp_path / "environment"
    env_path.mkdir()
    (env_path / "spack.yaml").write_text("spack:\n  specs: []\n  view: false\n")
    create = tmp_path / "create_environment.py"
    create.write_text(
        f"""
import sys
import spack.deptypes as dt
from spack.environment import Environment
from spack.spec import ArchSpec, Spec
from spack.variant import SingleValuedVariant

environment = Environment({str(env_path)!r})
compiler = Spec('builtin.llvm-amdgpu@=7.2.1', external_path={str(tmp_path / 'compiler')!r})
hip = Spec('builtin.hip@=7.2.1', external_path={str(tmp_path / 'hip')!r})
python = Spec('builtin.python@=' + '.'.join(map(str, sys.version_info[:3])),
              external_path=sys.prefix)
numpy = Spec('benchpark.py-numpy@=2.0', external_path={str(tmp_path / 'numpy')!r})
for name, spec in (
    ('raja-perf', 'raja-perf@=develop +rocm amdgpu_target=gfx942 build_system=cmake cxxflags="-O3"'),
    ('memtrace-llvm', 'benchpark.memtrace-llvm@=0.1.0 +runtime +python build_system=cmake'),
):
    root = Spec(spec, external_path={str(tmp_path)!r} + '/' + name)
    root.variants['build_system'] = SingleValuedVariant('build_system', 'cmake')
    root.add_dependency_edge(compiler, depflag=dt.BUILD, virtuals=('c', 'cxx'))
    root.add_dependency_edge(hip, depflag=dt.BUILD | dt.LINK | dt.RUN, virtuals=())
    if name == 'memtrace-llvm':
        root.add_dependency_edge(python, depflag=dt.BUILD | dt.RUN, virtuals=())
        root.add_dependency_edge(numpy, depflag=dt.RUN, virtuals=())
    for node in root.traverse():
        if node.architecture is None:
            node.architecture = ArchSpec.default_arch()
        for flag in ('cflags', 'cppflags', 'cxxflags', 'fflags', 'ldflags', 'ldlibs'):
            node.compiler_flags.setdefault(flag, [])
    root._mark_concrete()
    environment.add(name)
    environment.add_concrete_spec(Spec(name), root, new=False)
environment.write(regenerate=False)
"""
    )
    # Use the modifier's real subprocess runner. The wrapper only selects the
    # pinned Spack and package repositories for this test process.
    bin_path = tmp_path / "bin"
    bin_path.mkdir()
    wrapper = bin_path / "spack"
    builtin_repo = paths.benchpark_home / "spack-packages/repos/spack_repo/builtin"
    benchpark_repo = paths.benchpark_root / "repos/spack_repo/benchpark"
    command = [
        sys.executable,
        str(paths.global_spack_path / "bin/spack"),
        "-c",
        f"repos:builtin:{builtin_repo}",
        "-c",
        f"repos:benchpark:{benchpark_repo}",
    ]
    wrapper.write_text("#!/bin/sh\nexec " + shlex.join(command) + ' "$@"\n')
    wrapper.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_path) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("SPACK_USER_CACHE_PATH", str(tmp_path / "spack-cache"))
    monkeypatch.delenv("SPACK_ENV", raising=False)
    result = subprocess.run(
        ["spack", "python", str(create)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return env_path


@pytest.mark.parametrize("startup_banner", [False, True])
def test_root_info_through_spack_python_console(
    modifier, tmp_path, monkeypatch, metadata_environment, startup_banner
):
    env_path = metadata_environment
    startup = tmp_path / "pythonrc.py"
    startup.write_text("print('Ctrl click to launch VS Code Native REPL')\n")
    if startup_banner:
        monkeypatch.setenv("PYTHONSTARTUP", str(startup))
    else:
        monkeypatch.delenv("PYTHONSTARTUP", raising=False)
    benchmark = modifier._root_info(env_path, "raja-perf")
    plugin = modifier._root_info(env_path, "memtrace-llvm")
    assert benchmark["hash"] != plugin["hash"]
    assert len(benchmark["hash"]) == len(plugin["hash"]) == 32
    assert benchmark["compiler"] == plugin["compiler"]
    assert len(benchmark["compiler"]) == 32
    for name, info in (("raja-perf", benchmark), ("memtrace-llvm", plugin)):
        assert info["prefix"] == str(tmp_path / name)
        assert info["hip"] == str(tmp_path / "hip")
    assert benchmark["flags"]["cxxflags"] == ["-O3"]
    assert benchmark["targets"] == ["gfx942"]
    assert benchmark["rocm"] is True
    assert benchmark["cmake_root"] == "."
    assert plugin["rocm"] is False
    assert Path(plugin["python"]).samefile(sys.executable)
    assert plugin["reader_paths"][0] == str(
        tmp_path / "memtrace-llvm/share/memtrace/python"
    )
    assert plugin["reader_paths"][1:]
    assert plugin["reader_preload"] == []
    assert all(
        tmp_path / "numpy" in Path(path).parents and path.endswith("site-packages")
        for path in plugin["reader_paths"][1:]
    )

    if startup_banner:
        assert os.environ["PYTHONSTARTUP"] == str(startup)


@pytest.mark.parametrize("output", ["", "Unexpected startup banner\n{}"])
def test_root_info_reports_invalid_json(modifier, monkeypatch, capsys, output):
    monkeypatch.setattr(modifier, "_run_spack", lambda args: output)
    with pytest.raises(SystemExit):
        modifier._root_info("/test/environment", "raja-perf")
    error = capsys.readouterr().err
    assert "invalid JSON metadata for raja-perf" in error
    assert "/test/environment" in error
    assert f"Spack stdout: {output!r}" in error


def test_reader_uses_builtin_numpy_in_existing_environment(
    modifier, metadata_environment
):
    env_path = metadata_environment
    benchmark = modifier._root_info(env_path, "raja-perf")
    old_reader = modifier._root_info(env_path, "memtrace-llvm")
    modifier._use_builtin_numpy(env_path)
    reader = modifier._root_info(env_path, "memtrace-llvm")
    assert reader["hash"] != old_reader["hash"]
    manifest = (env_path / "spack.yaml").read_text()
    code = (
        "from spack.active_environment import active_environment; "
        "e = active_environment(); "
        "s = next(s for s in e.concrete_roots() if s.name == 'memtrace-llvm'); "
        "assert s['py-numpy'].namespace == 'builtin'; "
        "assert len(e.user_specs) == 2"
    )
    modifier._run_spack(["-e", env_path, "python", "-c", code])
    assert modifier._root_info(env_path, "raja-perf") == benchmark
    modifier._use_builtin_numpy(env_path)
    assert modifier._root_info(env_path, "memtrace-llvm") == reader
    assert (env_path / "spack.yaml").read_text() == manifest


@pytest.mark.parametrize("preserve", [False, True])
def test_spack_install_preserves_prepared_stage(
    modifier, tmp_path, monkeypatch, preserve
):
    # A real source install exercises Spack's stage destruction. The negative
    # control reproduces the default behavior that removed our CMake include.
    source = tmp_path / "source"
    source.mkdir()
    (source / "CMakeLists.txt").write_text("project(Probe)\n")
    archive = tmp_path / "probe.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(source, arcname="probe")
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    repo = tmp_path / "repo/spack_repo/memtrace_test"
    package = repo / "packages/memtrace_probe"
    package.mkdir(parents=True)
    (repo / "repo.yaml").write_text("repo:\n  namespace: memtrace_test\n  api: v2.0\n")
    (package / "package.py").write_text(
        f"""from spack.package import *
class MemtraceProbe(Package):
    homepage = 'https://example.com'
    version('1.0', sha256={checksum!r}, url={archive.as_uri()!r})
    def install(self, spec, prefix):
        mkdirp(prefix.share)
        install(join_path(self.stage.source_path, 'CMakeLists.txt'), prefix.share)
"""
    )
    env_path = tmp_path / "environment"
    env_path.mkdir()
    (env_path / "spack.yaml").write_text(
        "spack:\n  specs: []\n  view: false\n  mirrors:: {}\n"
    )
    create = tmp_path / "create.py"
    create.write_text(
        f"""from spack.environment import Environment
from spack.spec import Spec, ArchSpec, assign_hashes
from spack.variant import SingleValuedVariant
import spack.repo
spec = Spec('memtrace_test.memtrace-probe@=1.0')
spec.architecture = ArchSpec.default_arch()
spec.variants['build_system'] = SingleValuedVariant('build_system', 'generic')
for flag in ("cflags", "cppflags", "cxxflags", "fflags", "ldflags", "ldlibs"):
    spec.compiler_flags[flag] = []
assign_hashes([spec], repo=spack.repo.PATH)
environment = Environment({str(env_path)!r})
environment.add('memtrace-probe')
environment.add_concrete_spec(Spec('memtrace-probe'), spec)
environment.write(regenerate=False)
"""
    )
    wrapper = tmp_path / "bin/spack"
    wrapper.parent.mkdir()
    command = [
        sys.executable,
        str(paths.global_spack_path / "bin/spack"),
        "-c",
        f"repos:memtrace_test:{repo}",
        "-c",
        f"repos:benchpark:{paths.benchpark_root}/repos/spack_repo/benchpark",
        "-c",
        f"repos:builtin:{paths.benchpark_home}/spack-packages/repos/spack_repo/builtin",
        "-c",
        f"config:install_tree:root:{tmp_path}/store",
        "-c",
        f"config:build_stage:[{tmp_path}/stage]",
        "-c",
        f"config:source_cache:{tmp_path}/source-cache",
        "-c",
        f"config:misc_cache:{tmp_path}/misc-cache",
    ]
    wrapper.write_text("#!/bin/sh\nexec " + shlex.join(command) + ' "$@"\n')
    wrapper.chmod(0o755)
    monkeypatch.setenv("PATH", str(wrapper.parent) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("SPACK_USER_CACHE_PATH", str(tmp_path / "spack-cache"))
    monkeypatch.setenv("SPACK_DISABLE_LOCAL_CONFIG", "1")
    monkeypatch.delenv("SPACK_ENV", raising=False)
    modifier._run_spack(["python", create])
    modifier._run_spack(["-e", env_path, "stage", "memtrace-probe"])
    staged = modifier._run_spack(
        ["-e", env_path, "location", "--source-dir", "memtrace-probe"]
    )
    modifier._configure_cmake(
        staged, ".", tmp_path, "/plugin", "trace", modifier._options()
    )
    if preserve:
        modifier._install_root(env_path, "memtrace-probe", os.environ.copy())
    else:
        modifier._run_spack(
            [
                "-e",
                env_path,
                "install",
                "--only",
                "package",
                "--no-cache",
                "--keep-stage",
                "--dirty",
                "memtrace-probe",
            ]
        )
    prefix = modifier._run_spack(
        ["-e", env_path, "location", "--install-dir", "memtrace-probe"]
    )
    text = (Path(prefix) / "share/CMakeLists.txt").read_text()
    assert ("# BEGIN Benchpark compiler_memtrace" in text) is preserve


@pytest.mark.parametrize(
    "change", [None, "probe", "wrong_mode", "wrong_target", "empty"]
)
def test_catalogs_must_match_benchmark(modifier, tmp_path, change):
    source = tmp_path / "source"
    catalogs = tmp_path / "catalogs"
    catalogs.mkdir()
    metadata = {
        "ModuleName": str(source / "kernel.hip"),
        "Mode": "trace",
        "TargetCPU": "gfx942",
        "OpCount": 1,
    }
    if change == "probe":
        metadata["ModuleName"] = str(
            tmp_path / "build/CMakeFiles/CMakeHIPCompilerId.hip"
        )
    elif change == "wrong_mode":
        metadata["Mode"] = "count"
    elif change == "wrong_target":
        metadata["TargetCPU"] = "gfx906"
    elif change == "empty":
        metadata["OpCount"] = 0
    (catalogs / "kernel.device.json").write_text(json.dumps({"Metadata": metadata}))
    if change:
        with pytest.raises(SystemExit):
            modifier._validate_catalogs(catalogs, source, "trace", "gfx942")
    else:
        modifier._validate_catalogs(catalogs, source, "trace", "gfx942")


@pytest.mark.parametrize("mode", ["baseline", "count", "trace"])
def test_experiment_configuration(mode):
    experiment = (
        benchpark.spec.ExperimentSpec(f"saxpy+rocm compiler_memtrace={mode}")
        .concretize()
        .experiment
    )
    assert {
        "name": "compiler_memtrace",
        "mode": mode,
    } in experiment.compute_modifiers_section_wrapper()
    software = experiment.compute_package_section_wrapper()
    assert software["packages"]["memtrace_llvm"] == {
        "spack_pkg_spec": "memtrace-llvm +runtime +python",
        "compiler": "default-compiler",
    }


@pytest.mark.parametrize(
    "spec,message",
    [
        ("saxpy compiler_memtrace=trace", "requires \\+rocm"),
        (
            "raja-perf+rocm compiler_memtrace=trace package_manager=user-managed",
            "requires package_manager=spack",
        ),
        (
            "raja-perf+rocm compiler_memtrace=trace compiler_attribution=kru",
            "separate experiments",
        ),
    ],
)
def test_invalid_experiment_combinations(spec, message):
    with pytest.raises(BenchparkError, match=message):
        benchpark.spec.ExperimentSpec(
            spec
        ).concretize().experiment.compute_modifiers_section_wrapper()


def test_default_is_disabled():
    experiment = benchpark.spec.ExperimentSpec("saxpy+rocm").concretize().experiment
    assert all(
        m["name"] != "compiler_memtrace"
        for m in experiment.compute_modifiers_section_wrapper()
    )
    assert (
        "memtrace_llvm" not in experiment.compute_package_section_wrapper()["packages"]
    )


def test_trace_generates_separate_mpi_launches(modifier, app):
    command = CommandExecutable(
        "run", 'app --label "two words" --size {size}', mpi=True
    )
    before, after = modifier.compiler_memtrace("run", command, app)
    assert before[1].mpi and command.mpi
    assert "--mode count" in before[1].template[0]
    assert "--mode trace" in command.template[0]
    assert before[2].template == ["test $? -eq 0 || exit 1"]
    for template in (before[1].template[0], command.template[0]):
        assert template.endswith(' -- app --label "two words" --size {size}')
        assert "--ranks {n_ranks}" in template
    assert before[1].redirect != command.redirect
    assert not after


def test_unselected_commands_are_unchanged(modifier, app):
    command = CommandExecutable("prepare", "mkdir work")
    assert modifier.compiler_memtrace("prepare", command, app) == ([], [])
    assert command.template == ["mkdir work"]


@pytest.mark.parametrize("command", ["app && app", "app | tee log", ["app", "app"]])
def test_rejects_compound_commands(modifier, app, command):
    with pytest.raises(SystemExit):
        modifier.compiler_memtrace("run", CommandExecutable("run", command), app)


def test_build_flags_distinguish_modes_and_options(modifier):
    options = modifier._options()
    original = {"cxxflags": ["-O3"], "ldflags": ["-Wl,--export-dynamic"]}
    specs = {
        mode: modifier._instrumented_spec(
            "raja-perf+rocm", "/plugin", mode, options, original
        )
        for mode in ("baseline", "count", "trace")
    }
    assert len(set(specs.values())) == 3
    assert "-DMEMTRACE_COUNT" in specs["count"]
    assert "-DMEMTRACE_TRACE" in specs["trace"]
    assert "-DMEMTRACE_" not in specs["baseline"]
    for spec in specs.values():
        assert "-O3" in spec and "-Wl,--export-dynamic" in spec
        assert spec.index("libmemtrace_runtime.so") < spec.index("-Wl,--export-dynamic")
    options["prevectorize"] = "1"
    assert (
        modifier._instrumented_spec(
            "raja-perf+rocm", "/plugin", "count", options, original
        )
        != specs["count"]
    )


def test_flags_apply_to_root_before_compiler_and_dependencies(modifier):
    spec = modifier._instrumented_spec(
        'raja-perf cxxflags="-O3" %llvm-amdgpu ^hip cxxflags="-O1"',
        "/plugin",
        "count",
        modifier._options(),
        {"cxxflags": ["-O3"]},
    )
    root, dependencies = modifier._split_root_spec(spec)
    assert "-DMEMTRACE_COUNT" in root
    assert dependencies == '%llvm-amdgpu ^hip cxxflags="-O1"'
    assert spec != modifier._instrumented_spec(
        'raja-perf cxxflags="-O3" %llvm-amdgpu ^hip cxxflags="-O1"',
        "/plugin",
        "count",
        modifier._options(),
        {"cxxflags": ["-O3"]},
        context="other",
    )


def test_cmake_specs_keep_instrumentation_out_of_probe_flags(modifier):
    specs = {
        mode: modifier._instrumented_spec(
            "raja-perf+rocm",
            "/plugin",
            mode,
            modifier._options(),
            {"cxxflags": ["-O3"], "ldflags": ["-Wl,--export-dynamic"]},
            cmake=True,
        )
        for mode in ("baseline", "count", "trace")
    }
    assert len(set(specs.values())) == 3
    for spec in specs.values():
        assert "-O3" in spec and "-Wl,--export-dynamic" in spec
        assert "-include" not in spec and "-fpass-plugin" not in spec
        assert "libmemtrace_runtime.so" not in spec


@pytest.mark.parametrize("mode", ["baseline", "count", "trace"])
def test_cmake_hip_build(modifier, tmp_path, mode):
    # Enable with an installed plugin prefix and its matching ROCm toolchain.
    # No GPU is needed: this configures, compiles, links, and checks catalogs.
    plugin = os.environ.get("BENCHPARK_MEMTRACE_TEST_PREFIX")
    rocm = os.environ.get("BENCHPARK_MEMTRACE_TEST_ROCM")
    if not plugin or not rocm:
        pytest.skip(
            "set BENCHPARK_MEMTRACE_TEST_PREFIX and BENCHPARK_MEMTRACE_TEST_ROCM"
        )
    cmake = shutil.which("cmake")
    assert cmake is not None
    source = tmp_path / "source"
    source.mkdir()
    (source / "nested").mkdir()
    cmakelists = source / "CMakeLists.txt"
    cmakelists.write_text(
        "cmake_minimum_required(VERSION 3.24)\n"
        "project(MemtraceProbe LANGUAGES CXX HIP)\n"
        "add_subdirectory(nested)\n"
    )
    (source / "nested/CMakeLists.txt").write_text(
        "add_executable(probe probe.hip host.cpp)\n"
    )
    (source / "nested/probe.hip").write_text(
        "#include <hip/hip_runtime.h>\n"
        "__global__ void update(float *x) { x[threadIdx.x] += 1.0f; }\n"
        "int main() { return 0; }\n"
    )
    (source / "nested/host.cpp").write_text("int host_function() { return 1; }\n")
    catalogs = tmp_path / "catalogs"
    catalogs.mkdir()
    env = os.environ.copy()
    env.update(
        MEMTRACE_SRC_PATH=str(source),
        MEMTRACE_OUT_PATH=str(catalogs),
        MEMTRACE_ADDRSPACES="1:0",
        MEMTRACE_PREVECTORIZE="0",
        ROCM_PATH=rocm,
    )
    for name in ("HIPFLAGS", "CXXFLAGS", "MEMTRACE_WAVES_PER_EU"):
        env.pop(name, None)
    modifier._configure_cmake(source, ".", tmp_path, plugin, mode, modifier._options())
    contents = cmakelists.read_text()
    modifier._configure_cmake(source, ".", tmp_path, plugin, mode, modifier._options())
    assert cmakelists.read_text() == contents
    build = tmp_path / "build"
    compiler = str(Path(rocm) / "llvm/bin/amdclang++")
    for command in (
        [
            cmake,
            "-S",
            str(source),
            "-B",
            str(build),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_HIP_ARCHITECTURES=gfx942",
            f"-DCMAKE_HIP_COMPILER={compiler}",
            f"-DCMAKE_CXX_COMPILER={compiler}",
            f"-DCMAKE_PREFIX_PATH={rocm}",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        ],
        [cmake, "--build", str(build), "-j2"],
    ):
        result = subprocess.run(command, env=env, text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr
    assert (build / "nested/probe").is_file()
    assert list(catalogs.rglob("probe.hip.device.json"))
    commands = json.loads((build / "compile_commands.json").read_text())
    assert len(commands) == 2
    for entry in commands:
        assert "-fpass-plugin=" in entry["command"]
        if mode != "baseline":
            assert f"-DMEMTRACE_{mode.upper()}" in entry["command"]
            assert "memtrace_device.h" in entry["command"]


@pytest.mark.parametrize("fail_trace", [False, True])
@pytest.mark.parametrize("cmake", [False, True])
def test_setup_builds_distinct_prefixes_and_caches_only_success(
    modifier, app, tmp_path, monkeypatch, fail_trace, cmake
):
    (tmp_path / "spack.yaml").write_text(
        "spack:\n  specs: [raja-perf, memtrace-llvm]\n"
    )
    app.modifiers = []
    app.package_manager = SimpleNamespace(
        name="spack", _software_create_env=lambda *args: None
    )
    cached = []
    workspace = SimpleNamespace(
        dry_run=False,
        check_cache=lambda key: key in cached,
        add_to_cache=cached.append,
        software_environments=SimpleNamespace(_rendered_packages={}),
    )
    package = SimpleNamespace(spec_str=lambda **kwargs: "raja-perf+rocm %llvm-amdgpu")
    monkeypatch.setattr(modifier, "_benchmark_package", lambda *args: package)
    calls = []
    reader = tmp_path / "reader"
    reader.mkdir()
    (reader / "memtrace.py").write_text("class Run: pass\n")

    def info(env, name):
        data = dict(
            prefix=f"/{Path(env).name}/{name}",
            compiler="compiler",
            hip="/hip",
            targets=["gfx942"],
            rocm=True,
            flags={"cxxflags": ["-O3", "-include /header"]},
        )
        if cmake:
            data["cmake_root"] = "."
        if name == "memtrace-llvm":
            data.update(
                python=sys.executable,
                reader_paths=[str(reader)],
                reader_preload=[],
            )
        return data

    def spack(args, env=None):
        calls.append((args, env))
        if "--source-dir" in args:
            source = Path(args[1]) / "stage/spack-src"
            source.mkdir(parents=True, exist_ok=True)
            (source / "CMakeLists.txt").write_text("project(benchmark)\n")
            return str(source)
        if "--dirty" in args:
            if fail_trace and Path(args[1]).name == "trace":
                raise RuntimeError("trace build failed")
            (Path(env["MEMTRACE_OUT_PATH"]) / "kernel.device.json").write_text(
                json.dumps(
                    {
                        "Metadata": {
                            "ModuleName": str(
                                Path(env["MEMTRACE_SRC_PATH"]) / "kernel.hip"
                            ),
                            "Mode": Path(args[1]).name,
                            "TargetCPU": "gfx942",
                            "OpCount": 1,
                        }
                    }
                )
            )
        return ""

    monkeypatch.setattr(modifier, "_root_info", info)
    monkeypatch.setattr(modifier, "_run_spack", spack)
    if fail_trace:
        with pytest.raises(RuntimeError, match="trace build failed"):
            modifier._build_memtrace(workspace, app)
        assert not cached
        assert not Path(modifier._builds_file).exists()
        return
    modifier._build_memtrace(workspace, app)
    metadata = json.loads(Path(modifier._builds_file).read_text())
    assert metadata["prefixes"] == {
        "count": "/count/raja-perf",
        "trace": "/trace/raja-perf",
    }
    installs = [(args, env) for args, env in calls if "install" in args]
    instrumented = [(args, env) for args, env in installs if env is not None]
    assert len(instrumented) == 2
    for mode, (args, env) in zip(("count", "trace"), instrumented):
        if cmake:
            assert "memtrace_device.h" not in args[-1]
            config = Path(args[1]) / "memtrace.cmake"
            assert f"-DMEMTRACE_{mode.upper()}" in config.read_text()
            assert (
                str(config)
                in (Path(env["MEMTRACE_SRC_PATH"]) / "CMakeLists.txt").read_text()
            )
        else:
            assert f"-DMEMTRACE_{mode.upper()}" in args[-1]
        assert env["MEMTRACE_SRC_PATH"].endswith(f"/{mode}/stage/spack-src")
        assert env["MEMTRACE_OUT_PATH"].endswith(f"/{mode}/catalogs")
        assert "--no-cache" in args
        assert "--dont-restage" in args
        assert env["HIPFLAGS"] == "-O3 -include /header"
    assert all(env is None for args, env in installs if "dependencies" in args)
    assert len(cached) == 1
    before = len(calls)
    modifier._build_memtrace(workspace, app)
    assert len(calls) == before


def test_ramble_dryrun_orders_mpi_launches(tmp_path):
    import ramble.paths
    import yaml

    workspace = tmp_path / "workspace"
    config = workspace / "configs"
    env = os.environ.copy()
    env["PATH"] = str(paths.global_spack_path / "bin") + os.pathsep + env["PATH"]
    env["SPACK_USER_CACHE_PATH"] = str(tmp_path / "spack-cache")
    command = [sys.executable, ramble.paths.ramble_script]

    def ramble(*args):
        result = subprocess.run(
            command + list(args), env=env, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stdout + result.stderr

    ramble("workspace", "create", "-d", str(workspace))
    data = {
        "ramble": {
            "config": {"deprecated": True},
            "repos": [str(paths.benchpark_root / "repos/ramble_applications")],
            "modifier_repos": [str(paths.benchpark_root / "modifiers")],
            "variables": {
                "mpi_command": "mpirun -n {n_ranks}",
                "n_ranks": 2,
                "n_nodes": 1,
                "process_problem_size": 128,
            },
            "modifiers": [
                {"name": "exit-code"},
                {"name": "compiler_memtrace", "mode": "trace"},
            ],
            "applications": {
                "raja-perf": {
                    "workloads": {
                        "suite": {
                            "experiments": {
                                "test": {
                                    "variants": {
                                        "package_manager": "spack",
                                        "spack_install_compilers": False,
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "software": {
                "packages": {
                    "raja-perf": {
                        "spack_pkg_spec": "raja-perf+rocm amdgpu_target=gfx942"
                    }
                },
                "environments": {"raja-perf": {"packages": ["raja-perf"]}},
            },
        }
    }
    (config / "ramble.yaml").write_text(yaml.safe_dump(data))
    ramble("-D", str(workspace), "workspace", "concretize")
    ramble("-D", str(workspace), "workspace", "setup", "--dry-run")
    script = workspace / "experiments/raja-perf/suite/test/execute_experiment"
    text = script.read_text()
    assert (
        text.index("--mode count")
        < text.index("test $? -eq 0")
        < text.index("--mode trace")
    )
    assert text.count("mpirun -n 2 python3") == 2
    assert text.count("-- raja-perf.exe --size 128") == 2
    assert text.index("--mode trace") < text.index("Exit code for run")
    subprocess.run(["bash", "-n", str(script)], check=True)


def test_build_environment_preserves_configuration(modifier, tmp_path):
    import yaml

    parent = tmp_path / "parent"
    parent.mkdir()
    config = {
        "spack": {
            "specs": ["raja-perf", "memtrace-llvm"],
            "include": ["../config"],
            "view": "view",
            "packages": {"all": {"target": ["zen4"]}},
        }
    }
    (parent / "spack.yaml").write_text(yaml.safe_dump(config))
    child = parent / "compiler-memtrace/count"
    modifier._write_build_environment(
        parent, child, "raja-perf cxxflags=-DMEMTRACE_COUNT"
    )
    result = yaml.safe_load((child / "spack.yaml").read_text())["spack"]
    assert result["include"] == [str(tmp_path / "config")]
    assert result["view"] is False
    assert result["packages"] == config["spack"]["packages"]
    assert result["specs"] == ["raja-perf cxxflags=-DMEMTRACE_COUNT"]
    assert yaml.safe_load((parent / "spack.yaml").read_text()) == config


@pytest.fixture
def runner():
    source = paths.benchpark_root / "modifiers/compiler_memtrace/run.py"
    spec = importlib.util.spec_from_file_location("memtrace_runner", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "name",
    ["FLUX_TASK_RANK", "PMIX_RANK", "PMI_RANK", "OMPI_COMM_WORLD_RANK", "SLURM_PROCID"],
)
def test_rank_output_isolation(runner, name):
    assert runner.rank_id({name: "2"}, 4) == 2
    with pytest.raises(ValueError):
        runner.rank_id({name: "4"}, 4)
    with pytest.raises(ValueError):
        runner.rank_id({}, 4)


def test_map_spack_view_executable(runner, tmp_path, monkeypatch):
    original = tmp_path / "original"
    instrumented = tmp_path / "count"
    view = tmp_path / "view/bin"
    view.mkdir(parents=True)
    for prefix in (original, instrumented):
        (prefix / "bin").mkdir(parents=True)
        binary = prefix / "bin/app"
        binary.write_text("#!/bin/sh\nexit 0\n")
        binary.chmod(0o755)
    (view / "app").symlink_to(original / "bin/app")
    monkeypatch.setenv("PATH", str(view))
    assert runner.benchmark_command(["app", "two words"], original, instrumented) == [
        str(instrumented / "bin/app"),
        "two words",
    ]
    with pytest.raises(ValueError):
        runner.benchmark_command(["/bin/true"], original, instrumented)


@pytest.fixture
def runs(tmp_path):
    """A small valid count/trace pair, using the reader's public file ABI."""
    pytest.importorskip(
        "memtrace", reason="Set PYTHONPATH to memtrace-llvm/python to test the reader"
    )
    import numpy as np
    from memtrace.format import EVENT, HEADER

    catalog = {
        "Metadata": {"CatalogHash": "0123456789abcdef"},
        "Functions": [],
        "Ops": [
            {
                "op_id": 0,
                "kind": "load",
                "bytes": 8,
                "source_line": 1,
                "addrspace": 1,
            }
        ],
    }
    for mode in ("count", "trace"):
        directory = tmp_path / mode
        directory.mkdir()
        (directory / "catalog.json").write_text(json.dumps(catalog))
        np.array([0, 1], dtype="<u8").tofile(directory / "offsets.bin")
        info = {
            "mode": mode,
            "kernel": "kernel",
            "launch": 0,
            "grid": [1, 1, 1],
            "block": [64, 1, 1],
            "num_producers": 1,
            "total_events": 1,
            "catalog_hash": "0123456789abcdef",
            "catalog_file": "catalog.json",
            "offsets_file": "offsets.bin",
        }
        if mode == "count":
            info.update(counts_file="counts.bin", bb_count=1)
            np.array([1], dtype="<u4").tofile(directory / "counts.bin")
        else:
            info["trace_file"] = "trace.bin"
            header = np.zeros(1, dtype=HEADER)
            for key, value in dict(
                magic=b"MEMTRACE",
                version=3,
                header_bytes=64,
                record_bytes=528,
                wave_size=64,
                record_count=1,
                producer_count=1,
                catalog_hash=b"0123456789abcdef",
            ).items():
                header[key] = value
            events = np.zeros(1, dtype=EVENT)
            events["exec"] = 1
            events["address"][0, 0] = 1024
            (directory / "trace.bin").write_bytes(header.tobytes() + events.tobytes())
        (directory / "run_manifest.jsonl").write_text(json.dumps(info) + "\n")
    return tmp_path


def test_validate_trace_pair(runner, runs):
    assert runner.validate_pair(runs / "count", runs / "trace") == 1


@pytest.mark.parametrize(
    "change", ["empty", "missing", "duplicate", "geometry", "corrupt", "timing"]
)
def test_trace_failures_are_detected(runner, runs, change):
    manifest = runs / "trace/run_manifest.jsonl"
    record = json.loads(manifest.read_text())
    if change == "empty":
        manifest.write_text("")
    elif change == "missing":
        record["launch"] = 1
        manifest.write_text(json.dumps(record) + "\n")
    elif change == "duplicate":
        manifest.write_text(manifest.read_text() * 2)
    elif change == "geometry":
        record["grid"] = [2, 1, 1]
        manifest.write_text(json.dumps(record) + "\n")
    elif change == "corrupt":
        (runs / "trace/trace.bin").write_bytes(b"bad")
    with pytest.raises((ValueError, RuntimeError)):
        runner.validate_pair(runs / "count", runs / "trace", timing=change == "timing")


def test_wrapper_executes_build_and_rejects_reused_output(
    runner, runs, tmp_path, monkeypatch
):
    import memtrace

    prefix = tmp_path / "build"
    (prefix / "bin").mkdir(parents=True)
    app = prefix / "bin/app"
    app.write_text(
        f"#!{sys.executable}\nimport os, shutil, sys\n"
        f"shutil.copytree({str(runs / 'count')!r}, os.environ['MEMTRACE_RUN_OUT'], dirs_exist_ok=True)\n"
        "assert 'libm.so.6' not in os.environ.get('LD_PRELOAD', '')\n"
        "assert 'MEMTRACE_COUNT_RUN' not in os.environ\n"
        "assert sys.argv[1:] == ['two words']\n"
    )
    app.chmod(0o755)
    metadata = tmp_path / "builds.json"
    metadata.write_text(
        json.dumps(
            {
                "original": str(prefix),
                "prefixes": {"count": str(prefix)},
                "reader_paths": [str(Path(memtrace.__file__).parent.parent)],
                "reader_preload": ["libm.so.6"],
            }
        )
    )
    output = tmp_path / "output"
    monkeypatch.setenv("MEMTRACE_COUNT_RUN", "/unrelated/count")
    monkeypatch.delenv("LD_PRELOAD", raising=False)
    for name in (
        "FLUX_TASK_RANK",
        "PMIX_RANK",
        "PMI_RANK",
        "OMPI_COMM_WORLD_RANK",
        "SLURM_PROCID",
    ):
        monkeypatch.delenv(name, raising=False)
    command = [
        sys.executable,
        runner.__file__,
        "--builds",
        str(metadata),
        "--mode",
        "count",
        "--output",
        str(output),
        "--",
        str(app),
        "two words",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (output / "count/rank-0/validated.json").is_file()
    assert subprocess.run(command, capture_output=True).returncode != 0


def test_reader_import_failure_prevents_benchmark(runner, modifier, tmp_path, capsys):
    reader = tmp_path / "reader"
    reader.mkdir()
    (reader / "memtrace.py").write_text(
        'raise ImportError("test: unresolved BLAS symbol")\n'
    )
    plugin = {"python": sys.executable, "reader_paths": [str(reader)], "reader_preload": []}
    with pytest.raises(SystemExit):
        modifier._check_reader(plugin)
    assert "unresolved BLAS symbol" in capsys.readouterr().err

    prefix = tmp_path / "build"
    (prefix / "bin").mkdir(parents=True)
    marker = tmp_path / "benchmark-started"
    executable = prefix / "bin/app"
    executable.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
    executable.chmod(0o755)
    metadata = tmp_path / "builds.json"
    metadata.write_text(
        json.dumps(dict(plugin, original=str(prefix), prefixes={"count": str(prefix)}))
    )
    output = tmp_path / "output"
    result = subprocess.run(
        [
            sys.executable,
            runner.__file__,
            "--builds",
            str(metadata),
            "--mode",
            "count",
            "--output",
            str(output),
            "--",
            str(executable),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Cannot load the memtrace reader" in result.stderr
    assert "unresolved BLAS symbol" in result.stderr
    assert not marker.exists()
    assert not output.exists()
