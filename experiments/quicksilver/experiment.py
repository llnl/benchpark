# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment


class Quicksilver(Experiment):
    variant(
        "experiment",
        default="weak",
        values=("weak", "strong"),
        description="weak or strong scaling",
    )

    def compute_applications_section(self):
        variables = {}
        variants = {}

        variables["n_threads_per_proc"] = "1"
        variables["omp_num_threads"] = "{n_threads_per_proc}"
        variables["n_ranks"] = "{I}*{J}*{K}"
        variables["n"] = "{x}*{y}*{z}*10"
        variables["x"] = "{X}"
        variables["y"] = "{Y}"
        variables["z"] = "{Z}"
        if self.spec.satisfies("scaling=weak"):
            variables["X"] = ["32", "32", "64", "64"]
            variables["Y"] = ["32", "32", "32", "64"]
            variables["Z"] = ["16", "32", "32", "32"]
        else:
            variables["X"] = "32"
            variables["Y"] = "32"
            variables["Z"] = "16"
        variables["I"] = ["2", "2", "4", "4"]
        variables["J"] = ["2", "2", "2", "4"]
        variables["K"] = ["1", "2", "2", "2"]
        variants["package_manager"] = "spack"
        experiment_name_template = f"quicksilver_{self.spec.variants['experiment'][0]}"
        experiment_name_template += "{n_ranks}"
        return {
            "quicksilver": {  # ramble Application name
                "workloads": {
                    "quicksilver": {
                        "experiments": {
                            experiment_name_template: {
                                "variants": variants,
                                "variables": variables,
                            }
                        }
                    }
                }
            }
        }

    def compute_spack_section(self):
        # TODO: express that we need certain variables from system
        # Does not need to happen before merge, separate task
        qs_spack_spec = "quicksilver +openmp+mpi"
        packages = ["default-mpi", self.spec.name]

        return {
            "packages": {
                "quicksilver": {
                    "pkg_spec": qs_spack_spec,
                    "compiler": "default-compiler",
                }
            },
            "environments": {"quicksilver": {"packages": packages}},
        }
