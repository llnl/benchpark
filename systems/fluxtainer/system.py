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
        "arm": {"cpu_arch": "arm64"},
        "x86": {"cpu_arch": "x86_64_v3"},
    }

    variant(
        "instance_type",
        values=("arm", "x86"),
        default="x86",
        description="Target Architecture",
    )

    variant(
        "compiler",
        default="gcc",
        values=("clang", "gcc"),
        description="Which compiler to use",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [OpenMPCPUOnlySystem()]

        self.scheduler = "flux"
        setattr(self, "sys_cores_per_node", 8)
        setattr(self, "sys_mem_per_node_GB", 1)
        setattr(self, "n_nodes", 1)
        attrs = self.id_to_resources.get(self.spec.variants["instance_type"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_compilers_section(self):
        cfg = compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@14.3.1 languages=c,c++,fortran",
                    "/usr/",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                )
            ],
        )

        if (self.spec.satisfies("compiler=clang")):
            cfg = compiler_section_for(
                "clang",
                [
                    compiler_def(
                        "llvm@20.1.8",
                        "/usr/lib64/ccache/",
                        {"c": "clang", "cxx": "clang++"},
                    )
                ],
            )

        return cfg

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
                "bzip2": {
                    "externals": [{"spec": "bzip2@1.0.8", "prefix": "/usr"}],
                    "buildable": False,
                },
                "expat": {
                    "externals": [{"spec": "expat@2.7.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "gdbm": {
                    "externals": [{"spec": "gdbm@1.23", "prefix": "/usr"}],
                    "buildable": False,
                },
                "gettext": {
                    "externals": [{"spec": "gettext@0.22.5", "prefix": "/usr"}],
                    "buildable": False,
                },
                "libffi": {
                    "externals": [{"spec": "libffi@3.4.4", "prefix": "/usr"}],
                    "buildable": False,
                },
                "libxml2": {
                    "externals": [{"spec": "libxml2@2.12.5", "prefix": "/usr"}],
                    "buildable": False,
                },
                "ncurses": {
                    "externals": [{"spec": "ncurses@6.4", "prefix": "/usr"}],
                    "buildable": False,
                },
                "readline": {
                    "externals": [{"spec": "readline@8.2", "prefix": "/usr"}],
                    "buildable": False,
                },
                "sqlite": {
                    "externals": [{"spec": "sqlite@3.46.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "tar": {
                    "externals": [{"spec": "tar@1.35", "prefix": "/usr"}],
                    "buildable": False,
                },
                "util-linux-uuid": {
                    "externals": [{"spec": "util-linux-uuid@2.40.2", "prefix": "/usr"}],
                    "buildable": False,
                },
                "xz": {
                    "externals": [{"spec": "xz@5.6.2", "prefix": "/usr"}],
                    "buildable": False,
                },
                "zstd": {
                    "externals": [{"spec": "zstd@1.5.5", "prefix": "/usr"}],
                    "buildable": False,
                },
                "gmake": {
                    "externals": [{"spec": "gmake@4.4.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "pigz": {
                    "externals": [{"spec": "pigz@2.8.7", "prefix": "/usr"}],
                    "buildable": False,
                },
                "libmd": {
                    "externals": [{"spec": "libmd@1.2.0", "prefix": "/usr"}],
                    "buildable": False,
                },
                "libbsd": {
                    "externals": [{"spec": "libbsd@0.12.2", "prefix": "/usr"}],
                    "buildable": False,
                },
                "python": {
                    "externals": [{"spec": "python@3.12.12", "prefix": "/usr"}],
                    "buildable": False,
                },
            }
        }

    def compute_software_section(self):
        default_compiler = "gcc"
        if self.spec.satisfies("compiler=llvm"):
            default_compiler = "llvm"
        return {
            "software": {
                "packages": {
                    "default-compiler": {"pkg_spec": default_compiler},
                    "compiler-gcc": {"pkg_spec": "gcc"},
                    "default-mpi": {"pkg_spec": "mpich"},
                }
            }
        }
