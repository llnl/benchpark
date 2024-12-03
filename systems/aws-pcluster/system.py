# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.system import System
from benchpark.directives import variant

# Taken from https://aws.amazon.com/ec2/instance-types/
# With boto3, we could determine this dynamically vs. storing a static table
id_to_resources = {
    "c4.xlarge": {
        "sys_cores_per_node": 4,
        "sys_mem_per_node": 7.5,
    },
    "c6g.xlarge": {
        "sys_cores_per_node": 4,
        "sys_mem_per_node": 8,
    },
    "hpc7a.48xlarge": {
        "sys_cores_per_node": 96,
        "sys_mem_per_node": 768,
    },
    "hpc6a.48xlarge": {
        "sys_cores_per_node": 96,
        "sys_mem_per_node": 384,
    },
}


class Aws(System):
    variant(
        "instance_type",
        values=("c6g.xlarge", "c4.xlarge", "hpc7a.48xlarge", "hpc6a.48xlarge"),
        default="c4.xlarge",
        description="AWS instance type",
    )

    def initialize(self):
        super().initialize()
        self.scheduler = "slurm"
        # TODO: for some reason I have to index to get value, even if multi=False
        attrs = id_to_resources.get(self.spec.variants["instance_type"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def external_pkg_configs(self):
        externals = LlnlElcapitan.resource_location / "externals"

        selections = [
            externals / "base" / "00-packages.yaml",
        ]

        return selections

    def compiler_configs(self):
        compilers = LlnlElcapitan.resource_location / "compilers"

        selections = [
            compilers / "gcc" / "00-gcc-7-compilers.yaml",
        ]

        return selections

    def sw_description(self):
        return """\
software:
  packages:
    default-compiler:
      pkg_spec: gcc@7.3.1
    default-mpi:
      pkg_spec: openmpi@4.1.5%gcc@7.3.1
    compiler-gcc:
      pkg_spec: gcc@7.3.1
    lapack:
      pkg_spec: lapack@3.4.2
    mpi-gcc:
      pkg_spec: openmpi@4.1.5%gcc@7.3.1
"""
