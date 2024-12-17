# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.scaling import StrongScaling
from benchpark.scaling import WeakScaling

import os

class Ior(
    Experiment,
    StrongScaling,
    WeakScaling,
):
    variant(
        "workload",
        default="ior",
        description="base IOR  or other problem",
    )

    variant(
        "version",
        default="3.3.0",
        description="app version",
    )
    
    variant(
        "t",
        default="good",
        values=("small","medium","good","large"),
        description="transfer size",
    )

    variant(
        "a",
        default="POSIX",
        values=("POSIX","MPIIO","HDF5"),
        description="interface",
    )

    variant(
        "fileSys",
        default="lustre1",
        values=("lustre1","lustre2","lustre3","lustre4", "lustre5"),
        description="file system",
    )

    variant(
        "filePath",
        default="none",
        description="filePath",
    )
    
    def compute_applications_section(self):
        # TODO: Replace with conflicts clause
        scaling_modes = {
            "strong": self.spec.satisfies("+strong"),
            "weak": self.spec.satisfies("+weak"),
            "single_node": self.spec.satisfies("+single_node"),
        }

        scaling_mode_enabled = [key for key, value in scaling_modes.items() if value]
        if len(scaling_mode_enabled) != 1:
            raise BenchparkError(
                f"Only one type of scaling per experiment is allowed for application package {self.name}"
            )

        num_nodes = {"n_nodes": 1}
        t = ""
        self.add_experiment_variable("b", "256m", True)
        variants=self.spec._variants
        tSize=str(variants.dict.get("t",[])[0])
        if self.spec.satisfies("t=small"):
            t="16k"
        elif self.spec.satisfies("t=medium"):
            t="256k"
        elif self.spec.satisfies("t=good"):
            t="4m"
        elif self.spec.satisfies("t=large"):
            t="256m"
        filePath=str(variants.dict.get("filePath",[])[0])
        if not filePath.endswith('/'):
            filePath += '/'
        if os.path.exists(filePath):
            if os.access(filePath, os.R_OK):
                self.add_experiment_variable("o",'-o '+ filePath, False)
            else:
                raise BenchparkError(
                    f"You do not have permission to access {filePath}"
                )
        else:
            raise BenchparkError(
                f"The file path {filePath} does not exist"
            )
        if self.spec.satisfies("+single_node"):
            for pk, pv in num_nodes.items():
                self.add_experiment_variable(pk, pv, True)
            self.add_experiment_variable("t", t, True)
        elif self.spec.satisfies("+strong"):
            scaled_variables = self.generate_strong_scaling_params(
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)
            # 256 mb
            self.add_experiment_variable("t", t, True)
        elif self.spec.satisfies("+weak"):
            scaled_variables = self.generate_weak_scaling_params(
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                {tuple(num_nodes.keys()): list(num_nodes.values())},
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
            )
            for k, v in scaled_variables.items():
                self.add_experiment_variable(k, v, True)

            self.add_experiment_variable("t", t, True)

        self.add_experiment_variable(
            "n_ranks", "{sys_cores_per_node} * {n_nodes}", True
        )

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"

        # set package spack specs
        self.add_spack_spec(system_specs["mpi"])

        self.add_spack_spec(self.name, [f"ior@{app_version}", system_specs["compiler"]])
