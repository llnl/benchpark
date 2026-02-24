# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from enum import Enum

from benchpark.directives import requires, variant
from benchpark.experiment import ExperimentHelper


class ProgrammingModelType(Enum):
    Mpionly = "mpi"
    Openmp = "openmp"
    Cuda = "cuda"
    Rocm = "rocm"


def ProgrammingModel(*types):
    for ty in types:
        if not isinstance(ty, ProgrammingModelType):
            raise ValueError(f"Invalid programming model: {ty}")

    # Normalize once so we can reuse
    _available = tuple(t.value for t in types)

    class BaseModel:
        requires("mpi", when="+mpi")
        requires("rocm", when="+rocm")
        requires("cuda", when="+cuda")
        requires("openmp", when="+openmp")

        variant("mpi", default=True, description="Run with MPI")
        variant("rocm", default=False, description="Build and run with ROCm")
        variant("cuda", default=False, description="Build and run with CUDA")
        variant("openmp", default=False, description="Build and run with OpenMP")

        # Class-level list of supported models for any class that includes this mixin
        _available_programming_models = _available

        # Handy instance-level property (works on Experiment instances)
        @property
        def available_programming_models(self):
            # If multiple mixins contribute, merge them from MRO at runtime
            models = set()
            for cls in type(self).mro():
                models.update(getattr(cls, "_available_programming_models", ()))
            return tuple(sorted(models))

        # Quick check helper
        @staticmethod
        def supports_model(name: str) -> bool:
            return name in _available

    # Helper class (unchanged except for optional new method)
    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            models = []
            for s in [
                ProgrammingModelType.Mpionly.value,
                ProgrammingModelType.Openmp.value,
                ProgrammingModelType.Cuda.value,
                ProgrammingModelType.Rocm.value,
            ]:
                if self.spec.satisfies("+" + s):
                    models.append(s)
            if len(models) > 0:
                return models
            return "no_model"

        # Optional: expose *available* (not selected) models via helper, too
        def get_available_models(self):
            models = set()
            for cls in type(self).__mro__:
                models.update(getattr(cls, "_available_programming_models", ()))
            return tuple(sorted(models))

    return type(
        "ProgrammingModelType",
        (BaseModel,),
        {
            "Helper": Helper,
        },
    )
