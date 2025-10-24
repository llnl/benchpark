# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.cuda import CudaExperiment
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.openmp import OpenMPExperiment
from benchpark.rocm import ROCmExperiment


class Gromacs(
    Experiment,
    MpiOnlyExperiment,
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

    maintainers("pszi1ard")

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
        # MPI-only defaults
        self.add_experiment_variable("n_ranks", 8, True)
        target = "cpu"
        bonded_target = "cpu"
        npme = "0"

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

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{size}/{n_ranks}",
            total_problem_size="{size}",
        )

    def compute_package_section(self):
        spack_specs = "~hwloc"
        spack_specs += "+sycl" if self.spec.satisfies("+rocm") else "~sycl"

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            spack_specs += f" gpu-aware-mpi={self.spec.variants['gpu-aware-mpi'][0]} "
            spack_specs += " ~double "
        else:
            spack_specs += " gpu-aware-mpi=off "

        self.add_package_spec(
            self.name,
            [f"gromacs{self.determine_version()} {spack_specs}"],
        )
