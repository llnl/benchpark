# Copyright 2026 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.appkit import *


_FINITE = r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
_RANK_PREFIX = r"^\[rank (?P<rank>[0-9]+)\]\s+"
_TOTAL_TIME = rf"{_RANK_PREFIX}# Total Time \(s\)\s*:\s*(?P<total_time>{_FINITE})\s*$"
_AVERAGE_PERFORMANCE = (
    rf"{_RANK_PREFIX}# Average Performance\s*:\s*(?P<average_gflops>{_FINITE})"
    rf"\s+\+-\s+{_FINITE}\s*$"
)
_RANK_CONTEXT = r"^\[rank (?P<rank>[0-9]+)\]"


class Nbody(ExecutableApplication):
    """N-body benchmark from HeCBench."""

    name = "nbody"

    maintainers("chung38")
    tags("synthetic", "micro-benchmark", "gpu")

    with when("package_manager_family=spack"):
        software_spec("nbody", pkg_spec="hecbench")

    required_package("hecbench")

    executable(
        "nbody",
        "{hecbench_path}/bin/nbody-{model} {particle_count} {integration_steps}",
        use_mpi=True,
    )
    workload("nbody", executables=["nbody"])

    workload_variable(
        "model",
        default="hip",
        values=["hip", "cuda"],
        description="HeCBench programming-model suffix",
        workloads=["nbody"],
    )
    workload_variable(
        "particle_count",
        default="256",
        description="Number of N-body particles",
        workloads=["nbody"],
    )
    workload_variable(
        "integration_steps",
        default="3",
        description="Number of integration steps (at least three)",
        workloads=["nbody"],
    )

    log_file = "{experiment_run_dir}/{experiment_name}.out"

    figure_of_merit_context(
        "replica_rank", regex=_RANK_CONTEXT, output_format="rank {rank}"
    )

    figure_of_merit(
        "Average performance",
        log_file=log_file,
        fom_regex=_AVERAGE_PERFORMANCE,
        group_name="average_gflops",
        units="GFLOP/s",
        contexts=["replica_rank"],
        fom_type=FomType.THROUGHPUT,
    )
    figure_of_merit(
        "Total time",
        log_file=log_file,
        fom_regex=_TOTAL_TIME,
        group_name="total_time",
        units="s",
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
