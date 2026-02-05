# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import maintainers, variant
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from benchpark.paths import hardware_descriptions
from benchpark.system import System, compiler_def, compiler_section_for


class AwsPcluster(System):
    # Taken from https://aws.amazon.com/ec2/instance-types/
    # With boto3, we could determine this dynamically vs. storing a static table

    maintainers("wdhawkins")

    id_to_resources = {
        "c4.xlarge": {
            "sys_cores_per_node": 4,
            "sys_mem_per_node_GB": 7.5,
            "system_site": "aws",
            "hardware_key": str(hardware_descriptions)
            + "/AWS_PCluster-zen-EFA/hardware_description.yaml",
        },
        "c6g.xlarge": {
            "sys_cores_per_node": 4,
            "sys_mem_per_node_GB": 8,
            "system_site": "aws",
            "hardware_key": str(hardware_descriptions)
            + "/AWS_PCluster-zen-EFA/hardware_description.yaml",
        },
        "hpc7a.48xlarge": {
            "sys_cores_per_node": 96,
            "sys_mem_per_node_GB": 768,
            "system_site": "aws",
            "hardware_key": str(hardware_descriptions)
            + "/AWS_PCluster-zen-EFA/hardware_description.yaml",
        },
        "hpc6a.48xlarge": {
            "sys_cores_per_node": 96,
            "sys_mem_per_node_GB": 384,
            "system_site": "aws",
            "hardware_key": str(hardware_descriptions)
            + "/AWS_PCluster-zen-EFA/hardware_description.yaml",
        },
    }

    variant(
        "instance_type",
        values=("c6g.xlarge", "c4.xlarge", "hpc7a.48xlarge", "hpc6a.48xlarge"),
        default="c4.xlarge",
        description="AWS instance type",
    )

    variant(
        "scheduler",
        values=("slurm", "flux", "pbs"),
        default="slurm",
        description="Workload scheduler that will be used for this instance",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [OpenMPCPUOnlySystem()]

        self.scheduler = self.spec.variants["scheduler"][0]
        # TODO: for some reason I have to index to get value, even if multi=False
        attrs = self.id_to_resources.get(self.spec.variants["instance_type"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def system_specific_variables(self):
        return {
            "extra_cmd_opts": '--mpi=pmix --export=ALL,FI_EFA_USE_DEVICE_RDMA=1,FI_PROVIDER="efa",OMPI_MCA_mtl_base_verbose=100',
        }

    def compute_packages_section(self):
        return {
            "packages": {
                "tar": {
                    "externals": [{"spec": "tar@1.26", "prefix": "/usr"}],
                    "buildable": False,
                },
                "gmake": {"externals": [{"spec": "gmake@3.8.2", "prefix": "/usr"}]},
                "blas": {
                    "externals": [{"spec": "blas@3.4.2", "prefix": "/usr"}],
                    "buildable": False,
                },
                "lapack": {
                    "externals": [{"spec": "lapack@3.4.2", "prefix": "/usr"}],
                    "buildable": False,
                },
                "mpi": {"buildable": False},
                "openmpi": {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.5%gcc@7.3.1",
                            "prefix": "/opt/amazon/openmpi",
                            "extra_attributes": {
                                "ldflags": "-L/opt/amazon/openmpi/lib -lmpi"
                            },
                        }
                    ]
                },
            }
        }

    def compute_compilers_section(self):
        return compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@7.3.1 languages=c,c++,fortran",
                    "/usr/",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                )
            ],
        )

    def compute_software_section(self):
        return {
            "software": {
                "packages": {
                    "default-compiler": {"pkg_spec": "gcc@7.3.1"},
                    "default-mpi": {"pkg_spec": "openmpi@4.1.5%gcc@7.3.1"},
                    "compiler-gcc": {"pkg_spec": "gcc@7.3.1"},
                    "lapack": {"pkg_spec": "lapack@3.4.2"},
                    "mpi-gcc": {"pkg_spec": "openmpi@4.1.5%gcc@7.3.1"},
                }
            }
        }
