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
            "rocm_version": "6.4.0",
            "gtl_flag": True,
            "gpu_factor": 1,
            "extra_batch_opts": "--setattr=gpumode=SPX\n--conf=resource.rediscover=true",
        }
    }


def test_system_timeout():
    with pytest.raises(ValueError, match="is unsatisfiable for the selected queue"):
        sys_spec = benchpark.spec.SystemSpec(
            "llnl-elcapitan cluster=tioga queue=pdebug timeout=9999"
        ).concretize()
        sys_spec.system.compute_variables_section()
