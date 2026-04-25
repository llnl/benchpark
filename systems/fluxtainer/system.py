# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from benchpark.system import System, compiler_def, compiler_section_for


class Fluxtainer(System):
    """This is the generic system class for an x86 system, gcc compiler, mpi.
    It can be easily copied and modified to model other systems."""

    maintainers("nhanford")

    id_to_resources = {
        "arm": {
            "cpu_arch": "arm64",
            "sys_cores_per_node": 32,
            "sys_mem_per_node_GB": 1,
            "n_nodes": 4,
        },
        "x86": {
            "cpu_arch": "x86_64_v3",
            "sys_cores_per_node": 32,
            "sys_mem_per_node_GB": 1,
            "n_nodes": 4,
        }
    }

    variant(
        "instance_type",
        values=(
            "arm",
            "x86"
        ),
        default="x86",
        description="Target Architecture",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [OpenMPCPUOnlySystem()]

        self.scheduler = "flux"
        setattr(self, "sys_cores_per_node", 32)
        setattr(self, "sys_mem_per_node_GB", 2)
        attrs = self.id_to_resources.get(self.spec.variants["instance_type"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_compilers_section(self):
        return compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@14.3.1 languages=c,c++,fortran",
                    "/usr/",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                )
            ],
        )

    def compute_packages_section(self):
        return {
            "packages": {
                "mpi": {"buildable": False},
                "mpich": {
                    "externals": [
                        {
                            "spec": "mpich@4.1.2%gcc@14.3.1",
                            "prefix": "/usr/lib64/mpich",
                        }
                    ]
                },
                "cmake": {
                    "externals": [{"spec": "cmake@3.30.5", "prefix": "/usr"}],
                    "buildable": False,
                },
                "git": {
                    "externals": [{"spec": "git@2.47.3~tcltk", "prefix": "/usr"}],
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
                    "externals": [{"spec": "openssh@9.9p1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "m4": {
                    "externals": [{"spec": "m4@1.4.19", "prefix": "/usr"}],
                    "buildable": False,
                },
                "sed": {
                    "externals": [{"spec": "sed@4.9", "prefix": "/usr"}],
                    "buildable": False,
                },
                "autoconf": {
                    "externals": [{"spec": "autoconf@2.71", "prefix": "/usr"}],
                    "buildable": False,
                },
                "diffutils": {
                    "externals": [{"spec": "diffutils@3.10", "prefix": "/usr"}],
                    "buildable": False,
                },
                "coreutils": {
                    "externals": [{"spec": "coreutils@8.32", "prefix": "/usr"}],
                    "buildable": False,
                },
                "findutils": {
                    "externals": [{"spec": "findutils@4.10.0", "prefix": "/usr"}],
                    "buildable": False,
                },
                "binutils": {
                    "externals": [
                        {"spec": "binutils@2.41+gold~headers", "prefix": "/usr"}
                    ],
                    "buildable": False,
                },
                "perl": {
                    "externals": [
                        {
                            "spec": "perl@5.74.0~cpanm+opcode+open+shared+threads",
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
                        {"spec": "curl@8.12.1+gssapi+ldap+nghttp2", "prefix": "/usr"}
                    ],
                    "buildable": False,
                },
                "ccache": {
                    "externals": [{"spec": "ccache@4.11.3", "prefix": "/usr"}],
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
                "zlib-ng": {
                    "externals": [{"spec": "zlib-ng@2.2.3", "prefix": "/usr"}],
                    "buildable": False,
                },
                "ninja": {
                    "externals": [{"spec": "ninja@1.11.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "libtool": {
                    "externals": [{"spec": "libtool@2.4.7", "prefix": "/usr"}],
                    "buildable": False,
                },
            }
        }

    def compute_software_section(self):
        return {
            "software": {
                "packages": {
                    "compiler-gcc": {"pkg_spec": "gcc@14.3.1"},
                    "default-compiler": {"pkg_spec": "gcc"},
                    "compiler-gcc": {"pkg_spec": "gcc@14.3.1"},
                    "default-mpi": {"pkg_spec": "mpich"},
                }
            }
        }
