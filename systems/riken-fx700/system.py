# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from benchpark.paths import hardware_descriptions
from benchpark.system import System, compiler_def, compiler_section_for


class RikenFx700(System):

    maintainers("jdomke", "SBA0486")

    id_to_resources = {
        "fx700": {
            "sys_cores_per_node": 48,
            "sys_mem_per_node_GB": 32,
            "system_site": "rccs",
            "hardware_key": str(hardware_descriptions)
            + "/Fujitsu-A64FX-TofuD/hardware_description.yaml",
        },
    }

    variant(
        "compiler",
        default="fj",
        values=("clang", "gcc", "fj"),
        description="Which compiler to use",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [OpenMPCPUOnlySystem()]
        self.scheduler = "slurm"

        attrs = self.id_to_resources.get("fx700")
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
        if self.spec.satisfies("compiler=gcc"):
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

    def compute_compilers_section(self):
        compiler = self.spec.variants["compiler"][0]

        if compiler == "clang":
            return compiler_section_for(
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
        if compiler == "gcc":
            return compiler_section_for(
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
        return compiler_section_for(
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

    def system_specific_variables(self):
        return {
            "queue": "fx700",
            "pre_exec_cmds": "export SLURM_MPI_TYPE=pmix ; module load system/fx700 FJSVstclanga",
        }

    def compute_software_section(self):
        default_comp = self.spec.variants["compiler"][0]
        if default_comp == "clang":
            default_comp = "llvm"

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
