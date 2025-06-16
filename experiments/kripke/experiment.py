# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.new_scaling import ScalingMode, Scaling
from benchpark.caliper import Caliper


class Kripke(
    Experiment,
    OpenMPExperiment,
    CudaExperiment,
    ROCmExperiment,
    Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
    Caliper,
):
    variant(
        "workload",
        default="kripke",
        values=("kripke",),
        description="problem1 or problem2",
    )

    variant(
        "version",
        default="develop",
        description="app version",
    )

    maintainers("pearce8")

    def compute_applications_section(self):
        # Number of processes in each dimension
        self.add_experiment_variable("num_procs", {"npx": 2, "npy": 2, "npz": 1}, True)

        # Per-process size (in zones) in each dimension
        self.add_experiment_variable(
            "problem_sizes", {"nzx": 64, "nzy": 64, "nzz": 32}, True
        )

        self.add_experiment_variable("ngroups", 64, True)
        self.add_experiment_variable("gs", 1, True)
        self.add_experiment_variable("nquad", 128, True)
        self.add_experiment_variable("ds", 128, True)
        self.add_experiment_variable("lorder", 4, True)

        # Register the scaling variables and their respective scaling functions
        # required to correctly scale the experiment for the given scaliing config

        # The register_scaling_config method defines the scaled variables and their
        # scaling function for each scaling mode supported in the experiment
        # The input to register_scaling_config is a dictionary of the form
        # ScalingMode -> { scaled_var: scaling_function }
        # An entry is required for each ScalingMode supported in the experiment
        # For a multi-dimensional variable of the form:
        # num_procs -> { "px": 2, "py": 2, "pz": 1 }, the value of scaled_var is "num_procs"
        # For a scalar variable, the value of scaled_var is the name of the variable
        # Each scaled_var specified in register_scaling_config must be added to the
        # list of experiment variables using add_experiment_variable
        #
        # The scaling function has the following form
        # def scaling_function(var, itr, dim, scaling_factor):
        #    return ...
        # The arguments for the scaling_function are:
        # var: benchpark.Variable instance of the scaled variable
        # itr: The current iteration in the specified number of scaling iterations
        # dim: The current dimension that is being scaled
        # scaling_factor: The factor by which the variable dimension must be scaled
        # The scaling_function must return the new scaled value for the variable dimension
        #
        # scaling starts from the dimension with the minimum value for the first variable
        # in the list of variables and proceeds through the dimensions in a round-robin
        # manner for the specified number of scaling iterations
        # e.g. if the scaling config is defined as:
        # ScalingMode.Strong: {
        #     "np": lambda var, itr, dim, sf: var.val(dim) * sf,
        #     "probs": lambda var, itr, dim, sf: var.val(dim) * sf,
        # }, and the starting values of the variables are
        # "np" : { "px": 2,
        #          "py": 2,
        #          "pz": 1 } and,
        # "probs" : { "nx": 16,
        #             "ny": 32,
        #             "nz": 32 },
        # then after 4 scaling iterations (3 scalings), the
        # final values of the scaled variables will be
        # "np" : { "px": [2,2,4,4]
        #          "py": [2,2,2,4]
        #          "pz": [1,2,2,2] } and,
        # "probs" : { "nx": [16,16,32,32]
        #             "ny": [32,32,32,64]
        #             "nz": [32,64,64,64] },
        # Note that scaling starts with the minimum value dimension (pz) of the
        # first variable (np) and proceeds in a round-robin manner


        # In this application, since the input problem sizes (problem_sizes)
        # are global process sizes, strong scaling the problem requires that
        # only num_procs are scaled up, i.e. (x * scaling_factor),
        # problem_sizes remain unchanged

        # For weak scaling, both num_procs and problem_sizes
        # have to be scaled up i.e. (x * scaling_factor)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "num_procs": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "problem_sizes": lambda var, itr, dim, scaling_factor: var.val(dim),
                },
                ScalingMode.Weak: {
                    "num_procs": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "problem_sizes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
                ScalingMode.Throughput: {
                    "num_procs": lambda var, itr, dim, scaling_factor: var.val(dim),
                    "problem_sizes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
            }
        )

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{npx}*{npy}*{npz}",
            process_problem_size="{nzx}*{nzy}*{nzz}/({npx}*{npy}*{npz})",
            total_problem_size="{nzx}*{nzy}*{nzz}",
        )

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("arch", "OpenMP")
        elif self.spec.satisfies("+cuda"):
            self.add_experiment_variable("arch", "CUDA")
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("arch", "HIP")
        else:
            self.add_experiment_variable("arch", "Sequential")

        if self.spec.satisfies("+openmp"):
            self.add_experiment_variable("n_threads_per_proc", 1, True)
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)

    def compute_package_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(self.name, [f"kripke@{app_version} +mpi"])
