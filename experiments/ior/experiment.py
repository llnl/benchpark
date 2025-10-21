# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.mpi import MpiOnlyExperiment
from benchpark.scaling import ScalingMode, Scaling


class Ior(Experiment, MpiOnlyExperiment, Scaling(ScalingMode.Strong, ScalingMode.Weak)):
    variant(
        "workload",
        default="MPIIO",
        values=("MPIIO", "POSIX"),
        description="base IOR  or other problem",
    )

    variant(
        "version",
        default="4.0.0",
        values=("develop", "latest", "4.0.0"),
        description="app version",
    )

    maintainers("hariharan-devarajan")

    def compute_applications_section(self):

        if self.spec.satisfies("exec_mode=test"):
            nodes = 1
            bt_factor = 8  # blocksize = transfersize * bt_factor
            t = 524288
        elif self.spec.satisfies("exec_mode=perf"):
            nodes = 32
            bt_factor = 128  # blocksize = transfersize * bt_factor
            t = 67108864

        self.add_experiment_variable("n_nodes", nodes, True)
        self.add_experiment_variable("n_ranks", "4 * {n_nodes}", True)
        self.add_experiment_variable("t", t, True)
        self.add_experiment_variable("b", t * bt_factor, True)

        mount_point = self.system_spec.system.spec.variants["mount_point"][0]
        rabbit_config = self.system_spec.system.spec.variants.get(
            "rabbit_config", ["none"]
        )[0]
        sys_name = self.system_spec._name
        # Check mount point provided
        if mount_point == "none":
            raise ValueError(
                f'Must set "mount_point" variant (e.g. "benchpark system init {sys_name} mount_point=...") on the system used in this experiment. Run "benchpark info system {sys_name}" for valid values.'
            )
        elif rabbit_config != "none":
            full_path = f"$DW_JOB_{''.join(rabbit_config.split('_'))}" + "/test.bat"
        else:
            full_path = mount_point + "/$USER/test.bat"
        self.add_experiment_variable("o", full_path)

        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_nodes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "b": lambda var, itr, dim, scaling_factor: var.val(dim),
                },
                ScalingMode.Weak: {
                    "n_nodes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "b": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
            }
        )

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{b}/{n_ranks}",
            total_problem_size="{b}",
        )

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"ior{self.determine_version()}"])
