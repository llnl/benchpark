# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pytest

import benchpark.spec


def test_programming_model_checks():
    # babelstream mpi-only not valid
    with pytest.raises(NotImplementedError, match="cannot run with MPI only"):
        spec = benchpark.spec.ExperimentSpec("babelstream").concretize()
        experiment = spec.experiment  # noqa: F841

    # stream+openmp not valid
    with pytest.raises(Exception, match="not a valid variant"):
        spec = benchpark.spec.ExperimentSpec(
            "stream+openmp workload=stream"
        ).concretize()
