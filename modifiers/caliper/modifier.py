# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.modkit import *


def add_mode(mode_name, mode_option, description):
    mode(
        name=mode_name,
        description=description,
    )

    env_var_modification(
        "CALI_CONFIG_MODE",
        mode_option,
        method="append",
        separator=",",
        modes=[mode_name],
    )


class Caliper(SpackModifier):
    """Define a modifier for Caliper"""

    name = "caliper"

    tags("profiler", "performance-analysis")

    maintainers("pearce8")

    _cali_datafile = "{experiment_run_dir}/{experiment_name}.cali"

    _default_mode = "time"

    add_mode(
        mode_name=_default_mode,
        mode_option="time.exclusive",
        description="Platform-independent collection of time (default mode)",
    )

    env_var_modification(
        "CALI_CONFIG",
        "spot(output={}{})".format(_cali_datafile, "${CALI_CONFIG_MODE}"),
        method="set",
        modes=[_default_mode],
    )

    add_mode(
        mode_name="mpi",
        mode_option="profile.mpi",
        description="Profile MPI functions",
    )

    add_mode(
        mode_name="cuda",
        mode_option="profile.cuda",
        description="Profile CUDA API functions",
    )

    add_mode(
        mode_name="topdown-counters-all",
        mode_option="topdown-counters.all",
        description="Raw counter values for Intel top-down analysis (all levels)",
    )

    add_mode(
        mode_name="topdown-counters-toplevel",
        mode_option="topdown-counters.toplevel",
        description="Raw counter values for Intel top-down analysis (top level)",
    )

    add_mode(
        mode_name="topdown-all",
        mode_option="topdown.all",
        description="Top-down analysis for Intel CPUs (all levels)",
    )

    add_mode(
        mode_name="topdown-toplevel",
        mode_option="topdown.toplevel",
        description="Top-down analysis for Intel CPUs (top level)",
    )

    archive_pattern(_cali_datafile)

    software_spec("caliper", pkg_spec="caliper")

    required_package("caliper")
