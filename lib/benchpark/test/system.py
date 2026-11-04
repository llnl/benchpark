# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pickle
from types import SimpleNamespace

import pytest
import yaml

import benchpark.spec
from benchpark.cmd.experiment import experiment_init
from benchpark.cmd.system import system_init


@pytest.mark.parametrize(
    "system_spec",
    [
        "cscs-daint",
        "jcahpc-miyabi-g",
        "jsc-juwels",
        "lanl-venado cluster=grace-hopper",
        "lbnl-perlmutter",
        "llnl-matrix",
        "riken-dgx",
        "riken-gh200",
    ],
)
@pytest.mark.parametrize("experiment_spec", ["sparta-snl+cuda", "test.saxpy+cuda"])
def test_cuda_experiment_init_with_system(system_spec, experiment_spec, tmp_path):
    spec = benchpark.spec.SystemSpec(system_spec).concretize()
    spec.destdir = str(tmp_path)
    with (tmp_path / "system.pkl").open("wb") as stream:
        pickle.dump(spec, stream)

    experiment_init(
        SimpleNamespace(system=str(tmp_path), dest="experiment", spec=[experiment_spec])
    )

    with (tmp_path / "experiment" / "ramble.yaml").open() as stream:
        config = yaml.safe_load(stream)
    assert (
        config["ramble"]["config"]["system"]["name"] == spec.system.__class__.__name__
    )


def test_system_enforces_active_programming_models():
    cpu = benchpark.spec.SystemSpec("generic-x86").concretize().system
    gpu = benchpark.spec.SystemSpec("riken-dgx").concretize().system

    cpu.enforce("mpi")
    cpu.enforce("openmp")
    gpu.enforce("mpi")
    gpu.enforce("cuda")
    with pytest.raises(AttributeError, match='does not provide "cuda"'):
        cpu.enforce("cuda")
    with pytest.raises(AttributeError, match='does not provide "rocm"'):
        gpu.enforce("rocm")


def test_system_compute_variables_section(monkeypatch):
    sys_spec = benchpark.spec.SystemSpec("llnl-elcapitan cluster=tuolumne").concretize()
    system = sys_spec.system

    vars_section = system.compute_variables_section()

    assert vars_section == {
        "variables": {
            "timeout": "120",
            "scheduler": "flux",
            "sys_cores_per_node": 84,
            "n_ranks": 2**64 - 1,
            "n_nodes": 2**64 - 1,
            "batch_submit": "placeholder",
            "cpu_arch": "zen4",
            "mpi_command": "placeholder",
            "sys_cores_os_reserved_per_node": 12,
            "sys_cores_os_reserved_per_node_list": [
                0,
                8,
                16,
                24,
                32,
                40,
                48,
                56,
                64,
                72,
                80,
                88,
            ],
            "sys_gpus_per_node": 4,
            "sys_mem_per_node_GB": 512,
            "rocm_arch": "gfx942",
            "rocm_version": "6.4.3",
            "gtl_flag": True,
            "gpu_factor": 1,
            "extra_batch_opts": "-o spindle.level=off\n--amd-gpumode=SPX\n--conf=resource.rediscover=true",
        }
    }


@pytest.mark.parametrize("suffix", ["", " extra_batch_opts=none extra_cmd_opts=none"])
def test_system_extra_options_default_to_none(suffix):
    system = benchpark.spec.SystemSpec(f"generic-x86{suffix}").concretize().system
    variables = system.compute_variables_section()["variables"]

    assert "extra_batch_opts" not in variables
    assert "extra_cmd_opts" not in variables


def test_system_extra_options_append_to_system_defaults():
    default_system = (
        benchpark.spec.SystemSpec("llnl-elcapitan cluster=tuolumne").concretize().system
    )
    default_variables = default_system.compute_variables_section()["variables"]
    system = (
        benchpark.spec.SystemSpec(
            "llnl-elcapitan cluster=tuolumne "
            'extra_batch_opts="--requires=hosts:a,b" '
            'extra_cmd_opts="-o mpibind=greedy:0,verbose"'
        )
        .concretize()
        .system
    )
    variables = system.compute_variables_section()["variables"]

    assert variables["extra_batch_opts"] == (
        default_variables["extra_batch_opts"] + "\n--requires=hosts:a,b"
    )
    assert variables["extra_cmd_opts"] == "-o mpibind=greedy:0,verbose"


def test_system_extra_options_follow_trailing_newline():
    system = (
        benchpark.spec.SystemSpec('riken-fugaku extra_cmd_opts="--label output"')
        .concretize()
        .system
    )

    variables = system.compute_variables_section()["variables"]
    assert variables["extra_cmd_opts"] == "-std-proc fjmpioutdir/bmexe\n--label output"


def test_system_init_writes_extra_options_with_spaces_and_commas(tmp_path):
    destination = tmp_path / "system"
    system_init(
        SimpleNamespace(
            dest=str(destination),
            basedir=None,
            spec=[
                "generic-x86",
                "extra_batch_opts=--requires=hosts:a,b",
                "extra_cmd_opts=-o mpibind=greedy:0,verbose",
            ],
        )
    )

    with (destination / "variables.yaml").open() as stream:
        variables = yaml.safe_load(stream)["variables"]
    assert variables["extra_batch_opts"] == "--requires=hosts:a,b"
    assert variables["extra_cmd_opts"] == "-o mpibind=greedy:0,verbose"


@pytest.mark.parametrize(
    "gpumode,sys_gpus_per_node,gpu_factor",
    [
        ("SPX", 4, 1),
        ("TPX", 12, 3),
        ("CPX", 24, 6),
        ("SPXALL", 4, 1),
        ("TPXALL", 12, 3),
        ("CPXALL", 24, 6),
    ],
)
def test_mi300a_gpumode_options(gpumode, sys_gpus_per_node, gpu_factor):
    sys_spec = benchpark.spec.SystemSpec(
        f"llnl-elcapitan cluster=tuolumne gpumode={gpumode}"
    ).concretize()

    vars_section = sys_spec.system.compute_variables_section()["variables"]

    assert vars_section["sys_gpus_per_node"] == sys_gpus_per_node
    assert vars_section["gpu_factor"] == gpu_factor
    batch_options = vars_section["extra_batch_opts"].splitlines()
    assert f"--amd-gpumode={gpumode}" in batch_options
    assert not any(option.startswith("--setattr=gpumode=") for option in batch_options)


def test_system_timeout():
    with pytest.raises(ValueError, match="is unsatisfiable for the selected queue"):
        sys_spec = benchpark.spec.SystemSpec(
            "llnl-elcapitan cluster=tioga queue=pdebug timeout=9999"
        ).concretize()
        sys_spec.system.compute_variables_section()


def test_rocm7():
    sys_spec = benchpark.spec.SystemSpec(
        "llnl-elcapitan cluster=tuolumne rocm=7.2.0"
    ).concretize()
    sys_spec.system.compute_compilers_section()


@pytest.mark.parametrize(
    "version,rocm_prefix,llvm_prefix",
    [
        ("7.2.1", "/opt/rocm-7.2.1", "/opt/rocm-7.2.1/llvm"),
        ("7.14", "/opt/rocm/core-7.14", "/opt/rocm/core-7.14/lib/llvm"),
        ("10.0", "/opt/rocm/core-10.0", "/opt/rocm/core-10.0/lib/llvm"),
    ],
)
def test_rocm_install_prefix(version, rocm_prefix, llvm_prefix):
    sys_spec = benchpark.spec.SystemSpec(
        f"llnl-elcapitan cluster=tuolumne rocm={version}"
    ).concretize()
    system = sys_spec.system

    assert system.rocm_prefix == rocm_prefix
    assert system.rocm_llvm_prefix == llvm_prefix

    packages = system.rocm_config()["packages"]
    for package_name, package_config in packages.items():
        if "externals" not in package_config:
            continue
        expected_prefix = llvm_prefix if package_name == "llvm" else rocm_prefix
        assert package_config["externals"][0]["prefix"] == expected_prefix

    compiler_packages = system.rocm_cce_compiler_cfg()["packages"]
    rocm_compiler = compiler_packages["llvm-amdgpu"]["externals"][0]
    assert rocm_compiler["prefix"] == llvm_prefix
    compiler_attributes = rocm_compiler["extra_attributes"]
    assert all(
        path.startswith(f"{llvm_prefix}/bin/")
        for path in compiler_attributes["compilers"].values()
    )
    assert f"{rocm_prefix}/lib" in compiler_attributes["extra_rpaths"]

    cce_attributes = compiler_packages["cce"]["externals"][0]["extra_attributes"]
    cce_library_paths = cce_attributes["environment"]["prepend_path"][
        "LD_LIBRARY_PATH"
    ].split(":")
    assert f"{rocm_prefix}/lib" in cce_library_paths


def test_system_passthrough_opts_append():
    sys_spec = benchpark.spec.SystemSpec(
        "llnl-elcapitan cluster=elcapitan "
        "extra_batch_opts=--requires=hosts:elcap9376,elcap9800 "
        "extra_cmd_opts=--setopt=mpibind=greedy:0"
    ).concretize()

    vars_section = sys_spec.system.compute_variables_section()["variables"]

    batch_options = vars_section["extra_batch_opts"].splitlines()
    # The system's own options survive, and the user's come last, commas intact
    assert "--amd-gpumode=SPX" in batch_options
    assert batch_options[-1] == "--requires=hosts:elcap9376,elcap9800"
    assert vars_section["extra_cmd_opts"] == "--setopt=mpibind=greedy:0"


def test_system_init_accepts_literal_quotes(tmp_path):
    # CI expands SYSTEM_ARGS unquoted, so quotes reach benchpark literally and
    # values containing spaces arrive split across argv entries
    # (e.g. .gitlab/tests/nightly.yml: SYSTEM_ARGS: [mount_point="/p/lustre1"])
    dest = tmp_path / "dane"
    system_init(
        SimpleNamespace(
            spec=[
                "llnl-cluster",
                "cluster=dane",
                'mount_point="/p/lustre1"',
                'extra_cmd_opts="-o',
                'mpibind=greedy:0"',
                "timeout=60",
            ],
            dest=str(dest),
            basedir=None,
        )
    )

    assert "mount_point=/p/lustre1" in (dest / "system_id.yaml").read_text()
    with (dest / "variables.yaml").open() as stream:
        variables = yaml.safe_load(stream)["variables"]
    assert variables["extra_cmd_opts"] == "-o mpibind=greedy:0"
    assert variables["timeout"] == "60"
