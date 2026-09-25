# Copyright 2026 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.appkit import *


_FINITE = r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
_AVERAGE_TIME = (
    rf"^\[rank (?P<rank>[0-9]+)\]\s+Average kernel execution time:\s+"
    rf"(?P<average_time>{_FINITE})\s+\(ms\)\s*$"
)
_RANK_CONTEXT = r"^\[rank (?P<rank>[0-9]+)\]"


class Softmax(ExecutableApplication):
    """Softmax benchmark from HeCBench."""

    name = "softmax"

    maintainers("chung38")
    tags("synthetic", "micro-benchmark", "gpu")

    with when("package_manager_family=spack"):
        software_spec("softmax", pkg_spec="hecbench")

    required_package("hecbench")

    executable(
        "softmax",
        "{hecbench_path}/bin/softmax-{model} {num_slices} {slice_size} {implementation} "
        "{internal_repetitions}",
        use_mpi=True,
    )
    workload("softmax", executables=["softmax"])

    workload_variable(
        "model",
        default="hip",
        values=["hip", "cuda"],
        description="HeCBench programming-model suffix",
        workloads=["softmax"],
    )
    workload_variable(
        "num_slices",
        default="8",
        description="Number of independent Softmax slices",
        workloads=["softmax"],
    )
    workload_variable(
        "slice_size",
        default="128",
        description="Elements in each Softmax slice",
        workloads=["softmax"],
    )
    workload_variable(
        "implementation",
        default="1",
        values=["0", "1"],
        description="Softmax implementation selector",
        workloads=["softmax"],
    )
    workload_variable(
        "internal_repetitions",
        default="2",
        description="Repetitions measured by Softmax's native timer",
        workloads=["softmax"],
    )

    log_file = "{experiment_run_dir}/{experiment_name}.out"

    figure_of_merit_context(
        "replica_rank", regex=_RANK_CONTEXT, output_format="rank {rank}"
    )

    figure_of_merit(
        "Average kernel time",
        log_file=log_file,
        fom_regex=_AVERAGE_TIME,
        group_name="average_time",
        units="ms",
        contexts=["replica_rank"],
        fom_type=FomType.TIME,
    )

    success_criteria(
        "all_replicas_passed",
        mode="string",
        match=r"^OVERALL PASS \(([0-9]+)/\1 replica ranks\)$",
        file=log_file,
    )
    success_criteria(
        "no_replica_failed",
        mode="string",
        anti_match=r"^(?:\[rank [0-9]+\] )?FAIL$|^OVERALL FAIL",
        file=log_file,
    )
