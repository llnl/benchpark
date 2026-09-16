# Copyright 2026 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.appkit import *


_FINITE = r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
_TOTAL_TIME = rf"^# Total Time \(s\)\s*:\s*(?P<total_time>{_FINITE})\s*$"
_AVERAGE_PERFORMANCE = (
    rf"^# Average Performance\s*:\s*(?P<average_gflops>{_FINITE})"
    rf"\s+\+-\s+{_FINITE}\s*$"
)


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
        "nbody-{model} {particle_count} {integration_steps}",
        use_mpi=False,
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

    figure_of_merit(
        "Average performance",
        log_file=log_file,
        fom_regex=_AVERAGE_PERFORMANCE,
        group_name="average_gflops",
        units="GFLOP/s",
        fom_type=FomType.THROUGHPUT,
    )
    figure_of_merit(
        "Total time",
        log_file=log_file,
        fom_regex=_TOTAL_TIME,
        group_name="total_time",
        units="s",
        fom_type=FomType.TIME,
    )
