# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.modkit import *
from ramble.mod.benchpark.caliper import Caliper as CaliperBase


class CaliperTopdown(CaliperBase):
    """Define a modifier for Caliper"""

    name = "caliper-topdown"

    _cali_datafile = CaliperBase._cali_datafile

    env_var_modification(
        "CALI_CONFIG",
        "spot(output={}, topdown-counters.all)".format(_cali_datafile),
        method="set",
        modes=["topdown-counters-all"],
    )
    env_var_modification(
        "CALI_CONFIG",
        "spot(output={}, topdown-counters.toplevel)".format(_cali_datafile),
        method="set",
        modes=["topdown-counters-toplevel"],
    )
    env_var_modification(
        "CALI_CONFIG",
        "spot(output={}, topdown.all)".format(_cali_datafile),
        method="set",
        modes=["topdown-all"],
    )
    env_var_modification(
        "CALI_CONFIG",
        "spot(output={}, topdown.toplevel)".format(_cali_datafile),
        method="set",
        modes=["topdown-toplevel"],
    )
