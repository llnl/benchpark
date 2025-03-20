# Copyright 2024 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant, maintainers
from benchpark.experiment import Experiment
from benchpark.rocm import ROCmExperiment


class Scaffold(Experiment, ROCmExperiment):

    maintainers("michaelmckinsey1")

    variant(
        "workload",
        default="sweep",
        values=("sweep",),
    )

    variant("version", default="develop", description="app version")

    def compute_applications_section(self):
        self.add_experiment_variable("n_gpus", 1, True)
        self.add_experiment_variable("n_ranks", 1, True)

    def compute_package_section(self):
        app_version = self.spec.variants["version"][0]
        self.add_package_spec(
            self.name, [
                #f"scaffold@{app_version}", 
                "matplotlib==3.9.4","default-compiler"]
        )
        self.add_package_spec("test",
                              ["--index-url https://pypi.org/simple\n--extra-index-url https://download.pytorch.org/whl/rocm6.2\nmatplotlib==3.9.4\nnumpy==1.26.4\ntqdm==4.67.1\nwandb==0.19.6\nopen3d==0.18.0\npyntcloud==0.3.1\nPyYAML==6.0.2\ntorch==2.5.1+rocm6.2\ntorchvision==0.20.1+rocm6.2\ntorchaudio==2.5.1+rocm6.2\nmpi4py==4.0.2 --no-binary mpi4py\n", "default-compiler"])
