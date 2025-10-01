# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pytest

import benchpark.spec
from benchpark.error import BenchparkError


def test_programming_model_checks():
    # babelstream mpi-only not valid
    with pytest.raises(BenchparkError, match=r"mpi.*are not valid programming models"):
        spec = benchpark.spec.ExperimentSpec("babelstream").concretize()
        experiment = spec.experiment  # noqa: F841

    # stream+openmp not valid
    with pytest.raises(Exception, match="not a valid variant"):
        spec = benchpark.spec.ExperimentSpec(
            "stream+openmp workload=stream"
        ).concretize()
        experiment = spec.experiment

    # Multiple scaling options not valid
    with pytest.raises(BenchparkError, match="cannot specify multiple scaling options"):
        spec = benchpark.spec.ExperimentSpec("kripke+strong+weak").concretize()
        experiment = spec.experiment
