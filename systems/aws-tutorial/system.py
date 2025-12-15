# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from benchpark.paths import hardware_descriptions
from benchpark.system import System, compiler_def, compiler_section_for


class AwsTutorial(System):
    # Taken from https://aws.amazon.com/ec2/instance-types/
    # With boto3, we could determine this dynamically vs. storing a static table

    maintainers("stephanielam3211")

    id_to_resources = {
        "c7i.48xlarge": {
            "sys_cores_per_node": 192,
            "sys_mem_per_node_GB": 384,
        },
        "c7i.metal-48xl": {
            "sys_cores_per_node": 192,
            "sys_mem_per_node_GB": 384,
        },
        "c7i.24xlarge": {
            "sys_cores_per_node": 96,
            "sys_mem_per_node_GB": 192,
        },
        "c7i.metal-24xl": {
            "sys_cores_per_node": 96,
            "sys_mem_per_node_GB": 192,
        },
        "c7i.12xlarge": {
            "sys_cores_per_node": 48,
            "sys_mem_per_node_GB": 96,
        },
    }

    variant(
        "instance_type",
        values=(
            "c7i.48xlarge",
            "c7i.metal-48xl",
            "c7i.24xlarge",
            "c7i.metal-24xl",
            "c7i.12xlarge",
        ),
        default="c7i.24xlarge",
        description="AWS instance type",
    )

    def __init__(self, spec):
        super().__init__(spec)

        # Common attributes across instances
        self.programming_models = [OpenMPCPUOnlySystem()]
        self.system_site = "aws"
        self.scheduler = "flux"
        self.hardware_key = (
            str(hardware_descriptions)
            + "/AWS_Tutorial-sapphirerapids-EFA/hardware_description.yaml"
        )

        attrs = self.id_to_resources.get(self.spec.variants["instance_type"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):
        return {
            "packages": {
                "tar": {
                    "externals": [{"spec": "tar@1.34", "prefix": "/usr"}],
                    "buildable": False,
                },
                "gmake": {"externals": [{"spec": "gmake@4.3", "prefix": "/usr"}]},
                "blas": {"buildable": False},
                "lapack": {"buildable": False},
                "atlas": {
                    "externals": [{"spec": "atlas@3.10.3", "prefix": "/usr"}],
                },
                "mpi": {"buildable": False},
                "openmpi": {
                    "externals": [
                        {
                            "spec": "openmpi@4.0%gcc@11.4.0",
                            "prefix": "/usr",
                        }
                    ]
                },
                "cmake": {
                    "externals": [{"spec": "cmake@4.1.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "git": {
                    "externals": [{"spec": "git@2.34.1~tcltk", "prefix": "/usr"}],
                    "buildable": False,
                },
                "openssl": {
                    "externals": [{"spec": "openssl@3.0.2", "prefix": "/usr"}],
                    "buildable": False,
                },
                "automake": {
                    "externals": [{"spec": "automake@1.16.5", "prefix": "/usr"}],
                    "buildable": False,
                },
                "openssh": {
                    "externals": [{"spec": "openssh@8.9p1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "m4": {
                    "externals": [{"spec": "m4@1.4.18", "prefix": "/usr"}],
                    "buildable": False,
                },
                "sed": {
                    "externals": [{"spec": "sed@4.8", "prefix": "/usr"}],
                    "buildable": False,
                },
                "autoconf": {
                    "externals": [{"spec": "autoconf@2.71", "prefix": "/usr"}],
                    "buildable": False,
                },
                "diffutils": {
                    "externals": [{"spec": "diffutils@3.8", "prefix": "/usr"}],
                    "buildable": False,
                },
                "coreutils": {
                    "externals": [{"spec": "coreutils@8.32", "prefix": "/usr"}],
                    "buildable": False,
                },
                "findutils": {
                    "externals": [{"spec": "findutils@4.8.0", "prefix": "/usr"}],
                    "buildable": False,
                },
                "binutils": {
                    "externals": [
                        {"spec": "binutils@2.38+gold~headers", "prefix": "/usr"}
                    ],
                    "buildable": False,
                },
                "perl": {
                    "externals": [
                        {
                            "spec": "perl@5.34.0~cpanm+opcode+open+shared+threads",
                            "prefix": "/usr",
                        }
                    ],
                    "buildable": False,
                },
                "groff": {
                    "externals": [{"spec": "groff@1.22.4", "prefix": "/usr"}],
                    "buildable": False,
                },
                "curl": {
                    "externals": [
                        {"spec": "curl@7.81.0+gssapi+ldap+nghttp2", "prefix": "/usr"}
                    ],
                    "buildable": False,
                },
                "ccache": {
                    "externals": [{"spec": "ccache@4.5.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "flex": {
                    "externals": [{"spec": "flex@2.6.4+lex", "prefix": "/usr"}],
                    "buildable": False,
                },
                "pkg-config": {
                    "externals": [{"spec": "pkg-config@0.29.2", "prefix": "/usr"}],
                    "buildable": False,
                },
                "zlib": {
                    "externals": [{"spec": "zlib@1.2.11", "prefix": "/usr"}],
                    "buildable": False,
                },
                "ninja": {
                    "externals": [{"spec": "ninja@1.10.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "libtool": {
                    "externals": [{"spec": "libtool@2.4.6", "prefix": "/usr"}],
                    "buildable": False,
                },
            }
        }

    def compute_compilers_section(self):
        return compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@11.4.0 languages=c,c++,fortran",
                    "/usr/",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran-11"},
                )
            ],
        )

    def compute_software_section(self):
        return {
            "software": {
                "packages": {
                    "default-compiler": {"pkg_spec": "gcc@11.4.0"},
                }
            }
        }
