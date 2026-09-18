# Copyright 2026 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.appkit import *


_FINITE = r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
_RESULT_PREFIX = (_FINITE + r"\s*,\s*") * 12
_RESULT = (
    rf"^\s*{_RESULT_PREFIX}"
    rf"(?P<elapsed_time>{_FINITE})\s*,\s*{_FINITE}\s*,\s*"
    rf"(?P<tflops>{_FINITE})\s*$"
)


class Wmma(ExecutableApplication):
    """WMMA benchmark from HeCBench."""

    name = "wmma"

    maintainers("chung38")
    tags("synthetic", "micro-benchmark", "gpu")

    with when("package_manager_family=spack"):
        software_spec("wmma", pkg_spec="hecbench")

    required_package("hecbench")

    executable(
        "wmma",
        "wmma-{model} {implementation} {matrix_m} {matrix_n} {matrix_k} "
        "{internal_repetitions} {verify}",
        use_mpi=False,
    )
    workload("wmma", executables=["wmma"])

    workload_variable(
        "model",
        default="hip",
        values=["hip", "cuda"],
        description="HeCBench programming-model suffix",
        workloads=["wmma"],
    )
    workload_variable(
        "implementation",
        default="0",
        values=["0", "1"],
        description="WMMA implementation selector",
        workloads=["wmma"],
    )
    workload_variable(
        "matrix_m",
        default="16",
        description="WMMA matrix M dimension",
        workloads=["wmma"],
    )
    workload_variable(
        "matrix_n",
        default="16",
        description="WMMA matrix N dimension",
        workloads=["wmma"],
    )
    workload_variable(
        "matrix_k",
        default="64",
        description="WMMA matrix K dimension",
        workloads=["wmma"],
    )
    workload_variable(
        "internal_repetitions",
        default="1",
        description="Repetitions measured by WMMA's native timer",
        workloads=["wmma"],
    )
    workload_variable(
        "verify",
        default="1",
        values=["1"],
        description="Keep WMMA CPU verification enabled",
        workloads=["wmma"],
    )

    log_file = "{experiment_run_dir}/{experiment_name}.out"

    figure_of_merit(
        "Throughput",
        log_file=log_file,
        fom_regex=_RESULT,
        group_name="tflops",
        units="TFLOP/s",
        fom_type=FomType.THROUGHPUT,
    )
    figure_of_merit(
        "Elapsed time",
        log_file=log_file,
        fom_regex=_RESULT,
        group_name="elapsed_time",
        units="ms",
        fom_type=FomType.TIME,
    )
