# Copyright 2026 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from benchpark.cudasystem import CudaSystem
from benchpark.directives import ExperimentSystemBase
from benchpark.experiment import Experiment
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
from benchpark.rocmsystem import ROCmSystem
from benchpark.system import MPISystem


def test_programming_model_directives_stay_with_their_mixin():
    mpi = ProgrammingModel(ProgrammingModelType.Mpionly)
    cuda = ProgrammingModel(ProgrammingModelType.Cuda)

    # Create both helpers before either experiment to expose lost or leaked
    # directives in Ramble's class-creation staging area.
    class CpuExperiment(Experiment, mpi):
        pass

    class GpuExperiment(Experiment, cuda):
        pass

    cpu_variants = {
        name for variants in CpuExperiment.variants.values() for name in variants
    }
    gpu_variants = {
        name for variants in GpuExperiment.variants.values() for name in variants
    }
    assert "mpi" in cpu_variants
    assert "cuda" not in cpu_variants
    assert "cuda" in gpu_variants
    assert "mpi" not in gpu_variants
    assert {"exec_mode", "affinity", "hwloc", "githash"} <= cpu_variants & gpu_variants
    assert list(CpuExperiment.requires.values()) == [["mpi"]]
    assert list(GpuExperiment.requires.values()) == [["cuda"]]


@pytest.mark.parametrize(
    "mixin,capability",
    [
        (MPISystem, "mpi"),
        (CudaSystem, "cuda"),
        (ROCmSystem, "rocm"),
        (OpenMPCPUOnlySystem, "openmp"),
    ],
)
def test_system_inherits_mixin_capabilities(mixin, capability):
    class TestSystem(ExperimentSystemBase, mixin):
        pass

    assert TestSystem.provides == (capability,)
