# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.modkit import *
from ramble.mod.benchpark.caliper import Caliper as CaliperBase


class CaliperMpi(CaliperBase):
    """Define a modifier for Caliper"""

    name = "caliper-mpi"

    _cali_datafile = CaliperBase._cali_datafile

    env_var_modification(
        "CALI_CONFIG",
        "spot(output={},profile.mpi,mpi.message.size,mpi.message.count)".format(
            _cali_datafile
        ),
        method="set",
        modes=["mpi"],
    )
