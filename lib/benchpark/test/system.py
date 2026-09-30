# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pytest

import benchpark.spec


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
            "extra_batch_opts": "-o spindle.level=off\n--setattr=gpumode=SPX\n--conf=resource.rediscover=true",
        }
    }


@pytest.mark.parametrize(
    "gpumode,sys_gpus_per_node,gpu_factor,flux_option",
    [
        ("SPX", 4, 1, "--setattr=gpumode=SPX"),
        ("TPX", 12, 3, "--setattr=gpumode=TPX"),
        ("CPX", 24, 6, "--setattr=gpumode=CPX"),
        ("SPXALL", 4, 1, "--amd-gpumode=SPXALL"),
        ("TPXALL", 12, 3, "--amd-gpumode=TPXALL"),
        ("CPXALL", 24, 6, "--amd-gpumode=CPXALL"),
    ],
)
def test_mi300a_gpumode_options(gpumode, sys_gpus_per_node, gpu_factor, flux_option):
    sys_spec = benchpark.spec.SystemSpec(
        f"llnl-elcapitan cluster=tuolumne gpumode={gpumode}"
    ).concretize()

    vars_section = sys_spec.system.compute_variables_section()["variables"]

    assert vars_section["sys_gpus_per_node"] == sys_gpus_per_node
    assert vars_section["gpu_factor"] == gpu_factor
    batch_options = vars_section["extra_batch_opts"].splitlines()
    assert flux_option in batch_options
    if gpumode.endswith("ALL"):
        assert not any(
            option.startswith("--setattr=gpumode=") for option in batch_options
        )
    else:
        assert not any(option.startswith("--amd-gpumode=") for option in batch_options)


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
