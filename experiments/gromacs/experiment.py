# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment


class Gromacs(
    Experiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
):
    variant(
        "workload",
        default="water_gmx50_adac",
        description="workload name",
    )

    variant(
        "version",
        default="2024",
        values=("2024", "2023.3"),
        description="app version",
    )

    # off: turn off GPU-aware MPI
    # on: turn on, but allow groamcs to disable it if GPU-aware MPI is not supported
    # force: turn on and force gromacs to use GPU-aware MPI. May result in error if unsupported
    variant(
        "gpu-aware-mpi",
        default="on",
        values=("on", "off", "force"),
        description="Use GPU-aware MPI",
    )

    def compute_applications_section(self):
        if self.spec.satisfies("+openmp"):
            self.set_environment_variable("OMP_PROC_BIND", "close")
            self.set_environment_variable("OMP_PLACES", "cores")
            self.add_experiment_variable("n_threads_per_proc", 8, True)
            self.add_experiment_variable("n_ranks", 8, True)
            target = "cpu"
            bonded_target = "cpu"
            npme = "0"

        # Overrides +openmp settings
        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("n_gpus", 8, True)
            target = "gpu"
            bonded_target = "cpu"
            npme = "1"
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", 8, True)
            target = "gpu"
            bonded_target = "cpu"
            npme = "1"

        input_variables = {
            "target": f"{target}",
            "size": "1536",
            "dlb": "no",
            "pin": "off",
            "maxh": "0.05",
            "nsteps": "1000",
            "nstlist": "200",
            "npme": f"{npme}",
        }

        other_input_variables = {
            "nb": f"{target}",
            "pme": "auto",
            "bonded": f"{bonded_target}",
            "update": f"{target}",
        }

        for k, v in input_variables.items():
            self.add_experiment_variable(k, v, True)
        for k, v in other_input_variables.items():
            self.add_experiment_variable(k, v)

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        system_specs["blas"] = "default-blas"
        system_specs["lapack"] = "default-lapack"

        # set package spack specs
        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["mpi"])
        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["blas"])
        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["lapack"])

        spack_specs = "+mpi~hwloc"
        spack_specs += "+sycl" if self.spec.satisfies("+rocm") else "~sycl"

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            spack_specs += f" gpu-aware-mpi={self.spec.variants['gpu-aware-mpi'][0]} "
            spack_specs += " ~double "
        else:
            spack_specs += " gpu-aware-mpi=off "

        self.add_spack_spec(
            self.name,
            [f"gromacs@{app_version} {spack_specs}", system_specs["compiler"]],
        )
