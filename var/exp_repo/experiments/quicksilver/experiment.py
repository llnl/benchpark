# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.expr.builtin.caliper import Caliper

class Quicksilver(Experiment, Caliper):
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
        if self.spec.satisfies("experiment=weak"):
            variables["X"] =  ['24','24','36','48','60','48','84','48']
            variables["Y"] =  ['24','24','24','24','24','36','24','48']
            variables["Z"] =  ['12','24','24','24','24','24','24','24']
        else:
            variables["X"] = "32"
            variables["Y"] = "32"
            variables["Z"] = "16"
        variables["I"] = ['2','2','3','4','5','4','7','4']
        variables["J"] = ['2','2','2','2','2','3','2','4']
        variables["K"] = ['1','2','2','2','2','2','2','2']
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
    def compute_modifiers_section(self):
        return Experiment.compute_modifiers_section(
            self
        ) + Caliper.compute_modifiers_section(self)
    def compute_spack_section(self):
        # TODO: express that we need certain variables from system
        # Does not need to happen before merge, separate task
        package_specs= {}
        qs_spack_spec = "quicksilver@caliper +openmp+mpi+caliper"
        package_specs["quicksilver"] = {
	    "pkg_spec": "quicksilver@caliper +openmp+mpi+caliper",
 	    "compiler": "default-compiler",
        }
        caliper_package_specs = Caliper.compute_spack_section(self)
        packages = ["default-mpi", self.spec.name]

        return {
            "packages": {k: v for k, v in package_specs.items() if v}
            | caliper_package_specs["packages"],
            "environments": {
                "quicksilver":{
                    "packages": list(package_specs.keys())
                    + list(caliper_package_specs["packages"].keys())
                }
            },
        }
