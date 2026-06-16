# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from packaging.version import Version

from benchpark.cudasystem import CudaSystem
from benchpark.directives import maintainers, variant
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from benchpark.paths import hardware_descriptions
from benchpark.system import (
    System,
    compiler_def,
    compiler_section_for,
    merge_dicts,
)


class RikenCloud(System):

    maintainers("jdomke", "SBA0486")

    id_to_resources = {
        "fx700": {
            "sys_cores_per_node": 48,
            "sys_mem_per_node_GB": 32,
            "system_site": "rccs",
            "hardware_key": str(hardware_descriptions)
            + "/Fujitsu-A64FX-TofuD/hardware_description.yaml",
        },
        "gh200": {
            "sys_cores_per_node": 72,
            "sys_gpus_per_node": 1,
            "sys_mem_per_node_GB": 512,
            "system_site": "rccs",
            "queue": "qc-gh200",
            "hardware_key": str(hardware_descriptions)
            + "/NVIDIA-neoverse-GH200-Infiniband/hardware_description.yaml",
        },
        "dgx": {
            "sys_cores_per_node": 20,
            "sys_gpus_per_node": 1,
            "sys_mem_per_node_GB": 128,
            "system_site": "rccs",
            "queue": "ng-dgx-3h",
            "hardware_key": str(hardware_descriptions)
            + "/NVIDIA-cortex-GB10-Ethernet/hardware_description.yaml",
        },
        "genoa": {
            "sys_cores_per_node": 96,
            "sys_mem_per_node_GB": 768,
            "system_site": "rccs",
            "queue": "genoa",
            "hardware_key": str(hardware_descriptions)
            + "/AMD-zen4-EPYC-Ethernet/hardware_description.yaml",
        },
    }

    variant(
        "cluster",
        default="fx700",
        values=("fx700", "gh200", "genoa", "dgx"),
        description="Which cluster to run on",
    )
    variant(
        "compiler",
        default="fj",
        values=("clang", "gcc", "fj", "nvhpc", "cuda"),
        description="Which compiler to use",
    )
    variant(
        "cuda",
        default="12.9",
        values=("12.3", "12.4", "12.5", "12.6", "12.8", "12.9", "13.0", "13.1", "13.2"),
        description="CUDA version",
    )
    variant(
        "nvhpc",
        default="25.7",
        values=("26.3", "25.9", "25.7", "24.9", "24.3"),
        description="NVHPC version",
    )
    variant(
        "gtl",
        default=False,
        values=(True, False),
        description="Use GTL-enabled MPI",
    )

    def __init__(self, spec):
        super().__init__(spec)
        if self.spec.variants["cluster"][0] == "fx700":
            self.programming_models = [OpenMPCPUOnlySystem()]
            self.scheduler = "slurm"

        if self.spec.variants["cluster"][0] == "genoa":
            self.programming_models = [OpenMPCPUOnlySystem()]
            self.scheduler = "slurm"

        if self.spec.variants["cluster"][0] == "gh200":
            self.programming_models = [CudaSystem(), OpenMPCPUOnlySystem()]
            self.cuda_version = Version(self.spec.variants["cuda"][0])
            self.gtl_flag = self.spec.variants["gtl"][0]
            self.nvhpc_version = Version(self.spec.variants["nvhpc"][0])
            if str(self.nvhpc_version) == "26.3":
                self.cuda_version = "13.1"
            if str(self.nvhpc_version) == "25.9":
                self.cuda_version = "13.0"
            if str(self.nvhpc_version) == "25.7":
                self.cuda_version = "12.9"
            if str(self.nvhpc_version) == "24.9":
                self.cuda_version = "12.6"
            if str(self.nvhpc_version) == "24.3":
                self.cuda_version = "12.3"
            self.scheduler = "slurm"

        if self.spec.variants["cluster"][0] == "dgx":
            self.programming_models = [CudaSystem(), OpenMPCPUOnlySystem()]
            self.cuda_version = Version(self.spec.variants["cuda"][0])
            self.gtl_flag = self.spec.variants["gtl"][0]
            self.nvhpc_version = Version(self.spec.variants["nvhpc"][0])
            self.nvhpc_version = "26.3"
            if str(self.nvhpc_version) == "26.3":
                self.cuda_version = "13.1"
            self.scheduler = "slurm"

        attrs = self.id_to_resources.get(self.spec.variants["cluster"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):
        selections = {
            "packages": {
                "all": {
                    "providers": {
                        "mpi": ["fujitsu-mpi", "openmpi", "mpich"],
                        "blas": ["fujitsu-ssl2", "openblas"],
                        "lapack": ["fujitsu-ssl2", "openblas"],
                        "scalapack": ["fujitsu-ssl2", "netlib-scalapack"],
                        "fftw-api": ["fujitsu-fftw", "fftw", "rist-fftw"],
                    },
                    "permissions": {"write": "group"},
                },
            }
        }

        cluster = self.spec.variants["cluster"][0]
        if cluster == "fx700":
            selections["packages"] |= self.fx700_packages()["packages"]
        if cluster == "gh200":
            selections["packages"] |= self.gh200_packages()["packages"]
        if cluster == "dgx":
            selections["packages"] |= self.dgx_packages()["packages"]
        if cluster == "genoa":
            selections["packages"] |= self.genoa_packages()["packages"]

        return selections

    def fx700_packages(self):
        selections = {
            "packages": {
                "htslib": {"version": [1.12]},
                "python": {
                    "externals": [
                        {
                            "spec": "python@3.12.11 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "openssh": {"permissions": {"write": "user"}},
                "mpi": {
                    "buildable": False,
                },
                "autoconf": {
                    "externals": [
                        {
                            "spec": "autoconf@2.69 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "automake": {
                    "externals": [
                        {
                            "spec": "automake@1.16.1 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "binutils": {
                    "externals": [
                        {
                            "spec": "binutils@2.30 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "bzip2": {
                    "externals": [
                        {"spec": "bzip2@1.0.6 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "cmake": {
                    "externals": [
                        {
                            "spec": "cmake@3.26.5 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                    ]
                },
                "curl": {
                    "externals": [
                        {"spec": "curl@7.61.1 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "dbus": {
                    "externals": [
                        {"spec": "dbus@1.12.8 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "diffutils": {
                    "externals": [
                        {
                            "spec": "diffutils@3.6 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                    ]
                },
                "elfutils": {
                    "externals": [
                        {
                            "spec": "elfutils@0.190 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                    ]
                },
                "findutils": {
                    "externals": [
                        {
                            "spec": "findutils@4.6.0 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "fontconfig": {
                    "externals": [
                        {
                            "spec": "fontconfig@2.13.1 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "freetype": {
                    "externals": [
                        {
                            "spec": "freetype@2.9.1 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gmake": {
                    "externals": [
                        {"spec": "gmake@4.2.1 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                # "gdbm": {
                #     "externals": [
                #         {"spec": "gdbm@1.18 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                #     ]
                # },
                "gettext": {
                    "externals": [
                        {
                            "spec": "gettext@0.19.8.1 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gmp": {
                    "externals": [
                        {"spec": "gmp@6.1.2 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "gnutls": {
                    "externals": [
                        {
                            "spec": "gnutls@3.6.16 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                        {
                            "spec": "gnutls@3.6.14 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                    ]
                },
                # "hwloc": {
                #    "externals": [
                #        {"spec": "hwloc@2.2.0 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                #    ]
                # },
                "jansson": {
                    "externals": [
                        {
                            "spec": "jansson@2.14 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libaio": {
                    "externals": [
                        {
                            "spec": "libaio@0.3.112 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libdrm": {
                    "externals": [
                        {
                            "spec": "libdrm@2.4.108 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                        {
                            "spec": "libdrm@2.4.103 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                    ]
                },
                "libedit": {
                    "externals": [
                        {"spec": "libedit@3.1 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                # "libevent": {
                #    "externals": [
                #        {
                #            "spec": "libevent@2.1.8 arch=linux-rhel8-a64fx",
                #            "prefix": "/usr",
                #        }
                #    ]
                # },
                "libfabric": {
                    "externals": [
                        {
                            "spec": "libfabric@1.14.0 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libffi": {
                    "externals": [
                        {"spec": "libffi@3.1 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "libglvnd": {
                    "externals": [
                        {
                            "spec": "libglvnd@1.3.4 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libibumad": {
                    "externals": [
                        {
                            "spec": "libibumad@37.2 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                        {
                            "spec": "libibumad@32.0 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                    ]
                },
                "libiconv": {
                    "externals": [
                        {
                            "spec": "libiconv@2.28 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                    ]
                },
                "libpciaccess": {
                    "externals": [
                        {
                            "spec": "libpciaccess@0.14 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libpng": {
                    "externals": [
                        {
                            "spec": "libpng@1.6.34 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libtasn1": {
                    "externals": [
                        {
                            "spec": "libtasn1@4.13 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libtirpc": {
                    "externals": [
                        {
                            "spec": "libtirpc@1.1.4 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libtool": {
                    "externals": [
                        {
                            "spec": "libtool@2.4.6 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libuuid": {
                    "externals": [
                        {
                            "spec": "libuuid@2.32.1 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libxcb": {
                    "externals": [
                        {
                            "spec": "libxcb@1.13.1 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libxkbcommon": {
                    "externals": [
                        {
                            "spec": "libxkbcommon@0.9.1 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libxml2": {
                    "externals": [
                        {
                            "spec": "libxml2@2.9.7 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "lz4": {
                    "externals": [
                        {"spec": "lz4@1.8.3 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "m4": {
                    "externals": [
                        {"spec": "m4@1.4.18 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "ncurses": {
                    "externals": [
                        {
                            "spec": "ncurses@6.5 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "nettle": {
                    "externals": [
                        {
                            "spec": "nettle@3.4.1 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "nspr": {
                    "externals": [
                        {
                            "spec": "nspr@4.32.0 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                        {
                            "spec": "nspr@4.25.0 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                    ]
                },
                "numactl": {
                    "externals": [
                        {
                            "spec": "numactl@2.0.12 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "opengl": {
                    "externals": [{"spec": "opengl@4.5.0", "prefix": "/usr"}],
                },
                "openssl": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "openssl@1.1.1k arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                    ],
                },
                "papi": {
                    "externals": [
                        {"spec": "papi@5.6.0 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "pcre": {
                    "externals": [
                        {"spec": "pcre@8.42 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "pcre2": {
                    "externals": [
                        {"spec": "pcre2@10.32 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "perl": {
                    "externals": [
                        {"spec": "perl@5.26.3 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "pigz": {
                    "externals": [
                        {"spec": "pigz@2.4 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ],
                },
                "pkgconf": {
                    "externals": [
                        {
                            "spec": "pkgconf@1.4.2 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "popt": {
                    "externals": [
                        {"spec": "popt@1.18 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "readline": {
                    "externals": [
                        {
                            "spec": "readline@7.0 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "sqlite": {
                    "externals": [
                        {
                            "spec": "sqlite@3.26.0 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "tcl": {
                    "externals": [
                        {"spec": "tcl@8.6.8 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "ucx": {
                    "externals": [
                        {"spec": "ucx@1.11.2 arch=linux-rhel8-a64fx", "prefix": "/usr"},
                        {"spec": "ucx@1.9.0 arch=linux-rhel8-a64fx", "prefix": "/usr"},
                    ]
                },
                "valgrind": {
                    "externals": [
                        {
                            "spec": "valgrind@3.18.1 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                        {
                            "spec": "valgrind@3.16.0 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                    ]
                },
                "xz": {
                    "externals": [
                        {"spec": "xz@5.2.4 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
                "zlib": {
                    "externals": [
                        {"spec": "zlib@1.2.11 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ],
                },
                "zstd": {
                    "externals": [
                        {"spec": "zstd@1.4.4 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ],
                },
                "singularity": {
                    "externals": [
                        {
                            "spec": "singularity@4.3.2",
                            "prefix": "/usr",
                        }
                    ]
                },
            }
        }
        if self.spec.satisfies("compiler=gcc") or self.spec.satisfies("compiler=cuda"):
            selections["packages"] |= {
                "openmpi": {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.7",
                            "prefix": "/usr/mpi/gcc/openmpi-4.1.7rc1",
                            "extra_attributes": {
                                "ldflags": "-L/usr/mpi/gcc/openmpi-4.1.7rc1/lib64 -lmpi"
                            },
                        },
                    ],
                },
            }
        else:
            selections["packages"] |= {
                "fujitsu-mpi": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "fujitsu-mpi@4.11.1 arch=linux-rhel8-a64fx %fj@4.11.1",
                            "prefix": "/opt/FJSVstclanga/cp-1.0.30.01",
                        }
                    ],
                },
                "fujitsu-ssl2": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "fujitsu-ssl2@4.11.1 arch=linux-rhel8-a64fx %fj@4.11.1",
                            "prefix": "/opt/FJSVstclanga/cp-1.0.30.01",
                        }
                    ],
                },
            }
        return selections

    def gh200_packages(self):
        selections = {
            "packages": {
                "autoconf": {
                    "externals": [
                        {
                            "spec": "autoconf@2.69",
                            "prefix": "/usr",
                        }
                    ]
                },
                "automake": {
                    "externals": [
                        {
                            "spec": "automake@1.16.2",
                            "prefix": "/usr",
                        }
                    ]
                },
                "binutils": {
                    "externals": [
                        {
                            "spec": "binutils@2.35.2~gold~headers",
                            "prefix": "/usr",
                        }
                    ]
                },
                "bzip2": {
                    "externals": [
                        {
                            "spec": "bzip2@1.0.6 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "bison": {
                    "externals": [
                        {
                            "spec": "bison@3.7.4",
                            "prefix": "/usr",
                        }
                    ]
                },
                "cmake": {
                    "externals": [
                        {
                            "spec": "cmake@3.26.5",
                            "prefix": "/usr",
                        }
                    ]
                },
                "coreutils": {
                    "externals": [
                        {
                            "spec": "coreutils@8.32",
                            "prefix": "/usr",
                        }
                    ]
                },
                "curl": {
                    "externals": [
                        {
                            "spec": "curl@7.76.1+gssapi+ldap+nghttp2",
                            "prefix": "/usr",
                        }
                    ]
                },
                "diffutils": {
                    "externals": [
                        {
                            "spec": "diffutils@3.7",
                            "prefix": "/usr",
                        }
                    ]
                },
                "findutils": {
                    "externals": [
                        {
                            "spec": "findutils@4.8.0",
                            "prefix": "/usr",
                        }
                    ]
                },
                "flex": {
                    "externals": [
                        {
                            "spec": "flex@2.6.4+lex",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gawk": {
                    "externals": [
                        {
                            "spec": "gawk@5.1.0",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gettext": {
                    "externals": [
                        {
                            "spec": "gettext@0.21",
                            "prefix": "/usr",
                        }
                    ]
                },
                "git": {
                    "externals": [
                        {
                            "spec": "git@2.47.3~tcltk",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gmake": {
                    "externals": [
                        {
                            "spec": "gmake@4.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "groff": {
                    "externals": [
                        {
                            "spec": "groff@1.22.4",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libtool": {
                    "externals": [
                        {
                            "spec": "libtool@2.4.6",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libiconv": {
                    "externals": [
                        {
                            "spec": "libiconv@1.18",
                            "prefix": "/usr",
                        }
                    ]
                },
                "m4": {
                    "externals": [
                        {
                            "spec": "m4@1.4.19",
                            "prefix": "/usr",
                        }
                    ]
                },
                "openssh": {
                    "externals": [
                        {
                            "spec": "openssh@8.7p1",
                            "prefix": "/usr",
                        }
                    ]
                },
                "openssl": {
                    "externals": [
                        {
                            "spec": "openssl@3.2.2",
                            "prefix": "/usr",
                        }
                    ]
                },
                "perl": {
                    "externals": [
                        {
                            "spec": "perl@5.32.1~cpanm+opcode+open+shared+threads",
                            "prefix": "/usr",
                        }
                    ]
                },
                "pigz": {
                    "externals": [
                        {
                            "spec": "pigz@2.8",
                            "prefix": "/usr",
                        }
                    ],
                },
                "pkgconf": {
                    "externals": [
                        {
                            "spec": "pkgconf@1.7.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "python": {
                    "externals": [
                        {
                            "spec": "python@3.9.21+bz2+crypt+ctypes+dbm+lzma+pyexpat+pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib",
                            "prefix": "/usr",
                        }
                    ]
                },
                "sed": {
                    "externals": [
                        {
                            "spec": "sed@4.8",
                            "prefix": "/usr",
                        }
                    ]
                },
                "singularity": {
                    "externals": [
                        {
                            "spec": "singularity@4.3.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "slurm": {
                    "externals": [
                        {
                            "spec": "slurm@24.05.8",
                            "prefix": "/usr",
                        }
                    ]
                },
                "tar": {
                    "externals": [
                        {
                            "spec": "tar@1.34",
                            "prefix": "/usr",
                        }
                    ]
                },
                "xz": {
                    "externals": [
                        {
                            "spec": "xz@5.2.5",
                            "prefix": "/usr",
                        }
                    ]
                },
                "zlib": {
                    "externals": [
                        {
                            "spec": "zlib@1.2.11",
                            "prefix": "/usr",
                        }
                    ]
                },
                "zstd": {
                    "externals": [
                        {
                            "spec": "zstd@5.2.5",
                            "prefix": "/usr",
                        }
                    ]
                },
            }
        }
        if self.spec.satisfies("compiler=gcc") or self.spec.satisfies("compiler=cuda"):
            selections["packages"] |= {
                "openmpi": {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.7",
                            "prefix": "/usr/mpi/gcc/openmpi-4.1.7rc1",
                            "extra_attributes": {
                                "ldflags": "-L/usr/mpi/gcc/openmpi-4.1.7rc1/lib64 -lmpi"
                            },
                        },
                    ],
                },
            }
        if not self.spec.satisfies("compiler=cuda"):
            selections["packages"] |= self.cuda_config_gh200()["packages"]

        return selections

    def dgx_packages(self):
        selections = {
            "packages": {
                "autoconf": {
                    "externals": [
                        {
                            "spec": "autoconf@2.71",
                            "prefix": "/usr",
                        }
                    ]
                },
                "automake": {
                    "externals": [
                        {
                            "spec": "automake@1.16.5",
                            "prefix": "/usr",
                        }
                    ]
                },
                "binutils": {
                    "externals": [
                        {
                            "spec": "binutils@2.42",
                            "prefix": "/usr",
                        }
                    ]
                },
                "bzip2": {
                    "externals": [
                        {
                            "spec": "bzip2@1.0.8",
                            "prefix": "/usr",
                        }
                    ]
                },
                "bison": {
                    "externals": [
                        {
                            "spec": "bison@3.8.2",
                            "prefix": "/usr",
                        }
                    ]
                },
                "cmake": {
                    "externals": [
                        {
                            "spec": "cmake@3.28.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "coreutils": {
                    "externals": [
                        {
                            "spec": "coreutils@9.4",
                            "prefix": "/usr",
                        }
                    ]
                },
                "curl": {
                    "externals": [
                        {
                            "spec": "curl@8.5.0",
                            "prefix": "/usr",
                        }
                    ]
                },
                "diffutils": {
                    "externals": [
                        {
                            "spec": "diffutils@3.10",
                            "prefix": "/usr",
                        }
                    ]
                },
                "findutils": {
                    "externals": [
                        {
                            "spec": "findutils@4.9.0",
                            "prefix": "/usr",
                        }
                    ]
                },
                "flex": {
                    "externals": [
                        {
                            "spec": "flex@2.6.4",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gawk": {
                    "externals": [
                        {
                            "spec": "gawk@5.2.1",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gettext": {
                    "externals": [
                        {
                            "spec": "gettext@0.21",
                            "prefix": "/usr",
                        }
                    ]
                },
                "git": {
                    "externals": [
                        {
                            "spec": "git@2.43.0",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gmake": {
                    "externals": [
                        {
                            "spec": "gmake@4.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "groff": {
                    "externals": [
                        {
                            "spec": "groff@1.23.0",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libtool": {
                    "externals": [
                        {
                            "spec": "libtool@2.4.7",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libiconv": {
                    "externals": [
                        {
                            "spec": "libiconv@2.39",
                            "prefix": "/usr",
                        }
                    ]
                },
                "m4": {
                    "externals": [
                        {
                            "spec": "m4@1.4.19",
                            "prefix": "/usr",
                        }
                    ]
                },
                "openssh": {
                    "externals": [
                        {
                            "spec": "openssh@9.6p1",
                            "prefix": "/usr",
                        }
                    ]
                },
                "openssl": {
                    "externals": [
                        {
                            "spec": "openssl@3.0.13",
                            "prefix": "/usr",
                        }
                    ]
                },
                "perl": {
                    "externals": [
                        {
                            "spec": "perl@5.38.2",
                            "prefix": "/usr",
                        }
                    ]
                },
                "pkgconf": {
                    "externals": [
                        {
                            "spec": "pkgconf@1.8.1",
                            "prefix": "/usr",
                        }
                    ]
                },
                "python": {
                    "externals": [
                        {
                            "spec": "python@3.12.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "sed": {
                    "externals": [
                        {
                            "spec": "sed@4.9",
                            "prefix": "/usr",
                        }
                    ]
                },
                "singularity": {
                    "externals": [
                        {
                            "spec": "singularity@4.1.1",
                            "prefix": "/usr",
                        }
                    ]
                },
                "slurm": {
                    "externals": [
                        {
                            "spec": "slurm@24.05.8",
                            "prefix": "/usr",
                        }
                    ]
                },
                "tar": {
                    "externals": [
                        {
                            "spec": "tar@1.35",
                            "prefix": "/usr",
                        }
                    ]
                },
                "xz": {
                    "externals": [
                        {
                            "spec": "xz@5.4.5",
                            "prefix": "/usr",
                        }
                    ]
                },
                #                "zlib": {
                #                    "externals": [
                #                        {
                #                        "spec": "zlib@1.12",
                #                        "prefix": "/usr",
                #                        }
                #                    ]
                #                },
                "zstd": {
                    "externals": [
                        {
                            "spec": "zstd@1.5.5",
                            "prefix": "/usr",
                        }
                    ]
                },
            }
        }
        if self.spec.satisfies("compiler=nvhpc"):
            selections["packages"] |= {
                "openmpi": {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.9",
                            "prefix": "/opt/nvidia/hpc_sdk/Linux_aarch64/26.3/comm_libs/13.1/hpcx/hpcx-2.25.1/ompi",
                            "extra_attributes": {
                                "ldflags": "-L/opt/nvidia/hpc_sdk/Linux_aarch64/26.3/comm_libs/13.1/hpcx/hpcx-2.25.1/ompi -lmpi"
                            },
                        },
                    ],
                },
            }
        if not self.spec.satisfies("compiler=cuda"):
            selections["packages"] |= self.cuda_config_dgx()["packages"]

        return selections

    def genoa_packages(self):
        selections = {
            "packages": {
                "mpi": {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.1",
                            "prefix": "/usr/lib64/openmpi",
                            "extra_attributes": {
                                "ldflags": "-L/usr/lib64/openmpi/lib -lmpi"
                            },
                        },
                    ],
                },
                "pkgconf": {
                    "externals": [
                        {
                            "spec": "pkgconf@1.7.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "git": {
                    "externals": [
                        {
                            "spec": "git@2.47.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "cmake": {
                    "externals": [
                        {
                            "spec": "cmake@3.26.5",
                            "prefix": "/usr",
                        }
                    ]
                },
                "python": {
                    "externals": [
                        {
                            "spec": "python@3.9.25",
                            "prefix": "/usr",
                        }
                    ]
                },
                "m4": {
                    "externals": [
                        {
                            "spec": "m4@1.4.19",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gettext": {
                    "externals": [
                        {
                            "spec": "gettext@0.21",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gawk": {
                    "externals": [
                        {
                            "spec": "gawk@5.1.0",
                            "prefix": "/usr",
                        }
                    ]
                },
                "openssl": {
                    "externals": [
                        {
                            "spec": "openssl@3.5.1",
                            "prefix": "/usr",
                        }
                    ]
                },
                "bison": {
                    "externals": [
                        {
                            "spec": "bison@3.7.4",
                            "prefix": "/usr",
                        }
                    ]
                },
                "groff": {
                    "externals": [
                        {
                            "spec": "groff@1.22.4",
                            "prefix": "/usr",
                        }
                    ]
                },
                "tar": {
                    "externals": [
                        {
                            "spec": "tar@1.34",
                            "prefix": "/usr",
                        }
                    ]
                },
                "automake": {
                    "externals": [
                        {
                            "spec": "automake@1.16.2",
                            "prefix": "/usr",
                        }
                    ]
                },
                "flex": {
                    "externals": [
                        {
                            "spec": "flex@2.6.4",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gmake": {
                    "externals": [
                        {
                            "spec": "gmake@4.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "sed": {
                    "externals": [
                        {
                            "spec": "sed@4.8",
                            "prefix": "/usr",
                        }
                    ]
                },
                "autoconf": {
                    "externals": [
                        {
                            "spec": "autoconf@2.69",
                            "prefix": "/usr",
                        }
                    ]
                },
                "perl": {
                    "externals": [
                        {
                            "spec": "perl@5.32.1~cpanm+opcode+open+shared+threads",
                            "prefix": "/usr",
                        }
                    ]
                },
                "curl": {
                    "externals": [
                        {
                            "spec": "curl@7.76.1",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libtool": {
                    "externals": [
                        {
                            "spec": "libtool@2.4.6",
                            "prefix": "/usr",
                        }
                    ]
                },
                "singularity": {
                    "externals": [
                        {
                            "spec": "singularity@4.3.7",
                            "prefix": "/usr",
                        }
                    ]
                },
            }
        }

        return selections

    def cuda_config_gh200(self):
        cuda_version = self.cuda_version
        if self.spec.satisfies("compiler=nvhpc"):
            return {
                "packages": {
                    #    "blas": {"require": [f"{self.spec.variants['blas'][0]}"]},
                    #    "lapack": {"require": [f"{self.spec.variants['lapack'][0]}"]},
                    "cuda": {
                        "externals": [
                            {
                                "spec": f"cuda@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/cuda/{cuda_version}",
                                "modules": [
                                    "system/qc-gh200",
                                    f"nvhpc/{self.nvhpc_version}",
                                ],
                            }
                        ],
                        "buildable": False,
                    },
                    "curand": {
                        "externals": [
                            {
                                "spec": f"curand@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cusparse": {
                        "externals": [
                            {
                                "spec": f"cusparse@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cublas": {
                        "externals": [
                            {
                                "spec": f"cublas@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cusolver": {
                        "externals": [
                            {
                                "spec": f"cusolver@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cufft": {
                        "externals": [
                            {
                                "spec": f"cufft@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "openmpi": {
                        "buildable": True,
                        "version": ["4.1.7"],
                        "variants": "+cuda+cxx cuda_arch=90 fabrics=ucx schedulers=slurm",
                    },
                }
            }
        else:
            return {
                "packages": {
                    "cuda": {
                        "externals": [
                            {
                                "spec": f"cuda@{self.cuda_version}",
                                "prefix": f"/usr/local/cuda-{self.cuda_version}",
                            },
                        ],
                    },
                }
            }

    def cuda_config_dgx(self):
        cuda_version = self.cuda_version
        if self.spec.satisfies("compiler=nvhpc"):
            return {
                "packages": {
                    #    "blas": {"require": [f"{self.spec.variants['blas'][0]}"]},
                    #    "lapack": {"require": [f"{self.spec.variants['lapack'][0]}"]},
                    "cuda": {
                        "externals": [
                            {
                                "spec": f"cuda@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/cuda/{cuda_version}",
                                "modules": [
                                    "system/ng-dgx",
                                    f"nvhpc/{self.nvhpc_version}",
                                ],
                            }
                        ],
                        "buildable": True,
                    },
                    "curand": {
                        "externals": [
                            {
                                "spec": f"curand@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cusparse": {
                        "externals": [
                            {
                                "spec": f"cusparse@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cublas": {
                        "externals": [
                            {
                                "spec": f"cublas@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cusolver": {
                        "externals": [
                            {
                                "spec": f"cusolver@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cufft": {
                        "externals": [
                            {
                                "spec": f"cufft@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "openmpi": {
                        "buildable": True,
                        "version": ["4.1.7"],
                        "variants": "+cuda+cxx cuda_arch=90 fabrics=ucx schedulers=slurm",
                    },
                }
            }
        else:
            if str(self.cuda_version) != "13.0" and str(self.cuda_version) != "13.2":
                self.cuda_version = 13.2
            return {
                "packages": {
                    "cuda": {
                        "externals": [
                            {
                                "spec": f"cuda@{self.cuda_version}",
                                "prefix": f"/usr/local/cuda-{self.cuda_version}",
                            },
                        ],
                    },
                }
            }

    def compute_compilers_section(self):
        compiler = self.spec.variants["compiler"][0]
        cluster = self.spec.variants["cluster"][0]

        if cluster == "fx700":
            if compiler == "clang":
                cfg = compiler_section_for(
                    "llvm",
                    [
                        compiler_def(
                            "llvm@19.1.7+clang~flang+lld~lldb",
                            "/usr",
                            {"c": "clang", "cxx": "clang++"},
                            env={
                                "append_path": {
                                    "LD_LIBRARY_PATH": "/opt/FJSVstclanga/cp-1.0.30.01/lib64"
                                }
                            },
                        )
                    ],
                )
            elif compiler == "gcc":
                cfg = compiler_section_for(
                    "gcc",
                    [
                        compiler_def(
                            "gcc@8.5.0",
                            "/usr",
                            {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                            env={
                                "set": {
                                    "OPAL_PREFIX": "/opt/FJSVstclanga/cp-1.0.30.01/lib64"
                                },
                                "append_path": {
                                    "LD_LIBRARY_PATH": "/opt/FJSVstclanga/cp-1.0.30.01/lib64"
                                },
                            },
                        )
                    ],
                )
            elif compiler == "fj":
                cfg = compiler_section_for(
                    "fj",
                    [
                        compiler_def(
                            "fj@4.11.1",
                            "/opt/FJSVstclanga/cp-1.0.30.01/",
                            {"c": "fcc", "cxx": "FCC", "fortran": "frt"},
                            env={
                                "set": {
                                    "fcc_ENV": "-Nclang",
                                    "FCC_ENV": "-Nclang",
                                },
                                "prepend_path": {
                                    "PATH": "/opt/FJSVstclanga/cp-1.0.30.01/bin",
                                    "LD_LIBRARY_PATH": "/opt/FJSVstclanga/cp-1.0.30.01/lib64",
                                },
                            },
                        )
                    ],
                )
        elif cluster == "genoa":
            gcc_cfg = compiler_section_for(
                "gcc",
                [
                    compiler_def(
                        "gcc@11.5.0 languages:=c,c++,fortran",
                        "/usr/",
                        {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                    )
                ],
            )
            cfg = gcc_cfg

        elif cluster == "gh200":
            gcc_cfg = compiler_section_for(
                "gcc",
                [
                    compiler_def(
                        "gcc@11.5.0 languages:=c,c++,fortran",
                        "/usr/",
                        {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                    )
                ],
            )
            if self.spec.satisfies("compiler=cuda"):
                cuda_cfg = compiler_section_for(
                    "cuda",
                    [
                        compiler_def(
                            f"cuda@{self.cuda_version}",
                            f"/usr/local/cuda-{self.cuda_version}",
                            {"c": "nvcc", "cxx": "nvcc"},
                        )
                    ],
                )
                cfg = merge_dicts(cuda_cfg, gcc_cfg)
            elif self.spec.satisfies("compiler=nvhpc"):
                nvhpc_cfg = compiler_section_for(
                    "nvhpc",
                    [
                        compiler_def(
                            f"nvhpc@{self.nvhpc_version}",
                            f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/compilers",
                            {"c": "nvc", "cxx": "nvc++", "fortran": "nvfortran"},
                            extra_rpaths=[
                                f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/lib64",
                            ],
                            modules=[
                                "system/qc-gh200",
                                f"nvhpc/{self.nvhpc_version}",
                            ],
                        )
                    ],
                )
                cfg = nvhpc_cfg
            else:
                cfg = gcc_cfg

        elif cluster == "dgx":
            gcc_cfg = compiler_section_for(
                "gcc",
                [
                    compiler_def(
                        "gcc@13.3.0 languages:=c,c++,fortran",
                        "/usr/",
                        {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                    )
                ],
            )
            if self.spec.satisfies("compiler=cuda"):
                if (
                    str(self.cuda_version) != "13.0"
                    and str(self.cuda_version) != "13.2"
                ):
                    print("--- Change Notice ---")
                    print(
                        " The CUDA version has been changed to 13.2 (Restrictions in DGX)"
                    )
                    self.cuda_version = 13.2
                cuda_cfg = compiler_section_for(
                    "cuda",
                    [
                        compiler_def(
                            f"cuda@{self.cuda_version}",
                            f"/usr/local/cuda-{self.cuda_version}",
                            {"c": "nvcc", "cxx": "nvcc"},
                        )
                    ],
                )
                cfg = merge_dicts(cuda_cfg, gcc_cfg)
            elif self.spec.satisfies("compiler=nvhpc"):
                nvhpc_cfg = compiler_section_for(
                    "nvhpc",
                    [
                        compiler_def(
                            f"nvhpc@{self.nvhpc_version}",
                            f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/compilers",
                            {"c": "nvc", "cxx": "nvc++", "fortran": "nvfortran"},
                            extra_rpaths=[
                                f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/lib64",
                            ],
                            modules=[
                                "system/ng-dgx",
                                f"nvhpc/{self.nvhpc_version}",
                            ],
                        )
                    ],
                )
                cfg = nvhpc_cfg
            else:
                cfg = gcc_cfg

        return cfg

    def system_specific_variables(self):
        if self.spec.variants["cluster"][0] == "gh200":
            return {
                "cuda_arch": "90",
                "queue": "qc-gh200",
                "pre_exec_cmds": "export SLURM_MPI_TYPE=pmix",
            }
        if self.spec.variants["cluster"][0] == "dgx":
            return {
                "cuda_arch": "100",
                "queue": "ng-dgx-3h",
                "pre_exec_cmds": "export SLURM_MPI_TYPE=pmix",
            }
        if self.spec.variants["cluster"][0] == "fx700":
            return {
                "queue": "fx700",
                "pre_exec_cmds": "export SLURM_MPI_TYPE=pmix ; module load system/fx700 FJSVstclanga",
            }
        if self.spec.variants["cluster"][0] == "genoa":
            return {
                "queue": "genoa",
                "pre_exec_cmds": "export SLURM_MPI_TYPE=pmix",
            }

    def compute_software_section(self):
        default_comp = self.spec.variants["compiler"][0]
        if default_comp == "clang":
            default_comp = "llvm"

        if self.spec.variants["cluster"][0] == "fx700":
            return {
                "software": {
                    "packages": {
                        "default-compiler": {"pkg_spec": f"{default_comp}"},
                        "default-mpi": {"pkg_spec": "fujitsu-mpi"},
                        "compiler-clang": {"pkg_spec": "llvm"},
                        "compiler-fj": {"pkg_spec": "fj"},
                        "compiler-gcc": {"pkg_spec": "gcc"},
                        "blas": {"pkg_spec": "fujitsu-ssl2"},
                        "lapack": {"pkg_spec": "fujitsu-ssl2"},
                    }
                }
            }
        if self.spec.variants["cluster"][0] == "gh200":
            return {
                "software": {
                    "packages": {
                        "default-compiler": {"pkg_spec": f"{default_comp}"},
                        "default-mpi": {"pkg_spec": "openmpi"},
                        "compiler-gcc": {"pkg_spec": "gcc"},
                        "compiler-nvhpc": {"pkg_spec": "nvhpc"},
                        "cublas-cuda": {"pkg_spec": "cublas"},
                        "blas": {"pkg_spec": "openblas"},
                        "lapack": {"pkg_spec": "openblas"},
                    }
                }
            }
        if self.spec.variants["cluster"][0] == "dgx":
            return {
                "software": {
                    "packages": {
                        "default-compiler": {"pkg_spec": f"{default_comp}"},
                        "default-mpi": {"pkg_spec": "openmpi"},
                        "compiler-gcc": {"pkg_spec": "gcc"},
                        "compiler-nvhpc": {"pkg_spec": "nvhpc"},
                        "cublas-cuda": {"pkg_spec": "cublas"},
                        "blas": {"pkg_spec": "openblas"},
                        "lapack": {"pkg_spec": "openblas"},
                    }
                }
            }
        if self.spec.variants["cluster"][0] == "genoa":
            return {
                "software": {
                    "packages": {
                        "default-compiler": {"pkg_spec": f"{default_comp}"},
                        "default-mpi": {"pkg_spec": "openmpi"},
                        "compiler-gcc": {"pkg_spec": "gcc"},
                        "blas": {"pkg_spec": "openblas"},
                        "lapack": {"pkg_spec": "openblas"},
                    }
                }
            }
