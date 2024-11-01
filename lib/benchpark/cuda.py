# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper


class CudaExperiment:
    variant(
        "cuda",
        default="non",
        values=("oui", "non"),
        description="Build and run with CUDA",
    )

    class Helper(ExperimentHelper):
        def compute_spack_section(self):
            # get system config options
            # TODO: Get compiler/mpi/package handles directly from system.py
            system_specs = {}
            system_specs["compiler"] = "default-compiler"
            system_specs["cuda_version"] = "{default_cuda_version}"
            system_specs["cuda_arch"] = "{cuda_arch}"

            # set package spack specs
            package_specs = {}

            if self.spec.satisfies("cuda=oui"):
                package_specs["cuda"] = {
                    "pkg_spec": "cuda@{}+allow-unsupported-compilers".format(
                        system_specs["cuda_version"]
                    ),
                    "compiler": system_specs["compiler"],
                }

            return {
                "packages": {k: v for k, v in package_specs.items() if v},
                "environments": {"cuda": {"packages": list(package_specs.keys())}},
            }

        def get_helper_name_prefix(self):
            return "cuda" if self.spec.satisfies("cuda=oui") else ""

        def get_spack_variants(self):
            return (
                "+cuda cuda_arch={cuda_arch}"
                if self.spec.satisfies("cuda=oui")
                else "~cuda"
            )
