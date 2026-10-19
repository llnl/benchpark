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

    @staticmethod
    def is_available(mod):
        return mod in _available

    class BaseModel:
        if "mpi" in _available:
            requires("mpi", when="+mpi")
            variant("mpi", default=True, description="Run with MPI")
        if "rocm" in _available:
            requires("rocm", when="+rocm")
            variant("rocm", default=False, description="Build and run with ROCm")
        if "cuda" in _available:
            requires("cuda", when="+cuda")
            variant("cuda", default=False, description="Build and run with CUDA")
        if "openmp" in _available:
            requires("openmp", when="+openmp")
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

    # Helper class
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

        def get_spack_variants(self):
            models = []
            model_dict = {
                ProgrammingModelType.Openmp.value: ["+openmp", "~openmp"],
                ProgrammingModelType.Cuda.value: [
                    "+cuda cuda_arch={cuda_arch}",
                    "~cuda",
                ],
                ProgrammingModelType.Rocm.value: [
                    "+rocm amdgpu_target={rocm_arch}",
                    "~rocm",
                ],
            }
            for s in [
                ProgrammingModelType.Openmp.value,
                ProgrammingModelType.Cuda.value,
                ProgrammingModelType.Rocm.value,
            ]:
                if is_available(s):
                    if self.spec.satisfies("+" + s):
                        models.append(model_dict[s][0])
                    else:
                        models.append(model_dict[s][1])

            return " ".join(models)

    return type(
        "ProgrammingModelType",
        (BaseModel,),
        {
            "Helper": Helper,
        },
    )
