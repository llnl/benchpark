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
}


class Aws(System):
    variant(
        "instance_type",
        values=("c6g.xlarge", "c4.xlarge"),
        default="c4.xlarge",
        description="AWS instance type",
    )

    def initialize(self):
        super().initialize()
        self.scheduler = "mpi"
        # TODO: for some reason I have to index to get value, even if multi=False
        attrs = id_to_resources.get(self.spec.variants["instance_type"][0])
        for k, v in attrs.items():
            setattr(self, k, v)
