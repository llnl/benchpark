# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant, maintainers
from benchpark.system import System
from benchpark.openmpsystem import OpenMPSystem
from benchpark.paths import hardware_descriptions


class RikenFugaku(System):

    maintainers("jdomke", "SBA0486")

    id_to_resources = {
        "fugaku": {
            "sys_cores_per_node": 48,
            "sys_mem_per_node": 32,
            "system_site": "riken",
            "hardware_key": str(hardware_descriptions)
            + "/Fujitsu-A64FX-TofuD/hardware_description.yaml",
        },
    }

    variant(
        "compiler",
        default="clang",
        values=("clang", "gcc", "fj"),
        description="Which compiler to use",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [OpenMPSystem()]

        self.scheduler = "pjm"
        attrs = self.id_to_resources.get("fugaku")
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):
        # Doesn't look like we need to switch MPI based on compiler from old definition, verify this
        selections = {
            "packages": {
                "all": {
                    "compiler": ["clang", "fj", "gcc"],
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
                            "spec": "python@3.11.6%fj@4.10.0 arch=linux-rhel8-a64fx",
                            "prefix": "/vol0004/apps/oss/spack-v0.21/opt/spack/linux-rhel8-a64fx/fj-4.10.0/python-3.11.6-qbmpmn2uxu4oe3qoawxbizp7awqlgkcq",
                        }
                    ]
                },
                "openssh": {"permissions": {"write": "user"}},
                "fujitsu-mpi": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "fujitsu-mpi@4.10.0%clang@17.0.2 arch=linux-rhel8-a64fx",
                            "prefix": "/opt/FJSVxtclanga/tcsds-mpi-1.2.38",
                        },
                        {
                            "spec": "fujitsu-mpi@4.10.0%fj@4.10.0 arch=linux-rhel8-a64fx",
                            "prefix": "/opt/FJSVxtclanga/tcsds-mpi-1.2.38",
                        },
                        {
                            "spec": "fujitsu-mpi@4.10.0%gcc@13.2.0 arch=linux-rhel8-a64fx",
                            "prefix": "/vol0004/apps/oss/mpigcc/fjmpi-gcc12",
                        },
                    ],
                },
                "fujitsu-ssl2": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "fujitsu-ssl2@4.10.0%clang@17.0.2 arch=linux-rhel8-a64fx",
                            "prefix": "/vol0004/apps/oss/llvm-v17.0.2/compute_node",
                        },
                        {
                            "spec": "fujitsu-ssl2@4.10.0%fj@4.10.0 arch=linux-rhel8-a64fx",
                            "prefix": "/opt/FJSVxtclanga/tcsds-ssl2-1.2.38",
                        },
                        {
                            "spec": "fujitsu-ssl2@4.10.0%gcc@13.2.0 arch=linux-rhel8-a64fx",
                            "prefix": "/opt/FJSVxtclanga/tcsds-ssl2-1.2.38",
                        },
                    ],
                },
                "rist-fftw": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "rist-fftw@3.3.9-272-g63d6bd70 arch=linux-rhel8-a64fx",
                            "prefix": "/vol0004/share/rist/fftw/gcc-10.3.0/3.3.9-272-g63d6bd70",
                        }
                    ],
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
                            "spec": "cmake@3.27.7 arch=linux-rhel8-a64fx",
                            "prefix": "/vol0004/apps/oss/spack/opt/spack/linux-rhel8-a64fx/fj-4.10.0/cmake-3.27.7-ussgjuqkqbxi5dcv7kbp6bugdcjc5ph6",
                        },
                        {
                            "spec": "cmake@3.20.2 arch=linux-rhel8-a64fx",
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
                "elfutils": {
                    "externals": [
                        {
                            "spec": "elfutils@0.186 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                        {
                            "spec": "elfutils@0.182 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                    ]
                },
                "expat": {
                    "externals": [
                        {"spec": "expat@2.2.5 arch=linux-rhel8-a64fx", "prefix": "/usr"}
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
                "gdbm": {
                    "externals": [
                        {"spec": "gdbm@1.18 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
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
                "hwloc": {
                    "externals": [
                        {"spec": "hwloc@2.2.0 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ]
                },
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
                "libcap": {
                    "externals": [
                        {"spec": "libcap@2.48 arch=linux-rhel8-a64fx", "prefix": "/usr"}
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
                "libevent": {
                    "externals": [
                        {
                            "spec": "libevent@2.1.8 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
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
                    "buildable": False,
                    "externals": [{"spec": "opengl@4.5.0", "prefix": "/usr"}],
                },
                "openssl": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "openssl@1.1.1k arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        },
                        {
                            "spec": "openssl@1.1.1g arch=linux-rhel8-a64fx",
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
                    "buildable": False,
                    "externals": [
                        {"spec": "zlib@1.2.11 arch=linux-rhel8-a64fx", "prefix": "/usr"}
                    ],
                },
                "pmlib": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "pmlib@9.0-clang-precise arch=linux-rhel8-a64fx",
                            "prefix": "/vol0004/apps/oss/pmlib-v9.0/9.0-clang-precise",
                        },
                        {
                            "spec": "pmlib@9.0-clang-power arch=linux-rhel8-a64fx",
                            "prefix": "/vol0004/apps/oss/pmlib-v9.0/9.0-clang-power",
                        },
                        {
                            "spec": "pmlib@9.0-trad-power arch=linux-rhel8-a64fx",
                            "prefix": "/vol0004/apps/oss/pmlib-v9.0/9.0-trad-power",
                        },
                    ],
                },
            }
        }

        return selections

    def compute_compilers_section(self):

        compiler = self.spec.variants["compiler"][0]

        selections = {"compilers": []}

        if compiler == "clang":
            selections["compilers"] += [
                {
                    "compiler": {
                        "spec": "clang@17.0.2",
                        "paths": {
                            "cc": "/vol0004/apps/oss/llvm-v17.0.2/compute_node/bin/clang",
                            "cxx": "/vol0004/apps/oss/llvm-v17.0.2/compute_node/bin/clang++",
                            "f77": "/vol0004/apps/oss/llvm-v17.0.2/compute_node/bin/flang",
                            "fc": "/vol0004/apps/oss/llvm-v17.0.2/compute_node/bin/flang",
                        },
                        # Uncomment and populate these if needed
                        # "flags": {
                        #     "cflags": {"-msve-vector-bits=scalable"},
                        #     "cxxflags": {"-msve-vector-bits=scalable"},
                        #     "fflags": {"-msve-vector-bits=scalable"},
                        #     "ldflags": {"-fuse-ld=lld"},
                        # },
                        "environment": {
                            "append_path": {
                                "LD_LIBRARY_PATH": "/opt/FJSVxtclanga/tcsds-1.2.38/lib64"
                            }
                        },
                        "operating_system": "rhel8",
                        "target": "aarch64",
                        "modules": [],
                        "extra_rpaths": [],
                    }
                }
            ]
        elif compiler == "gcc":
            selections["compilers"] += [
                {
                    "compiler": {
                        "spec": "gcc@13.2.0",
                        "paths": {
                            "cc": "/vol0004/apps/oss/spack-v0.21/opt/spack/linux-rhel8-a64fx/gcc-8.5.0/gcc-13.2.0-abihbe7ykvpedq54j6blfvfppy7ojbmd/bin/gcc",
                            "cxx": "/vol0004/apps/oss/spack-v0.21/opt/spack/linux-rhel8-a64fx/gcc-8.5.0/gcc-13.2.0-abihbe7ykvpedq54j6blfvfppy7ojbmd/bin/g++",
                            "f77": "/vol0004/apps/oss/spack-v0.21/opt/spack/linux-rhel8-a64fx/gcc-8.5.0/gcc-13.2.0-abihbe7ykvpedq54j6blfvfppy7ojbmd/bin/gfortran",
                            "fc": "/vol0004/apps/oss/spack-v0.21/opt/spack/linux-rhel8-a64fx/gcc-8.5.0/gcc-13.2.0-abihbe7ykvpedq54j6blfvfppy7ojbmd/bin/gfortran",
                        },
                        "flags": {"ldflags": {"-lelf -ldl"}},
                        "environment": {
                            "set": {
                                "OPAL_PREFIX": "/vol0004/apps/oss/mpigcc/fjmpi-gcc12"
                            },
                            "append_path": {
                                "LD_LIBRARY_PATH": "/opt/FJSVxtclanga/tcsds-1.2.38/lib64"
                            },
                        },
                        "operating_system": "rhel8",
                        "target": "aarch64",
                        "modules": [],
                        "extra_rpaths": [],
                    }
                }
            ]
        elif compiler == "fj":
            selections["compilers"] += [
                {
                    "compiler": {
                        "spec": "fj@4.10.0",
                        "modules": [],
                        "paths": {
                            "cc": "/opt/FJSVxtclanga/tcsds-1.2.38/bin/fcc",
                            "cxx": "/opt/FJSVxtclanga/tcsds-1.2.38/bin/FCC",
                            "f77": "/opt/FJSVxtclanga/tcsds-1.2.38/bin/frt",
                            "fc": "/opt/FJSVxtclanga/tcsds-1.2.38/bin/frt",
                        },
                        "flags": {},
                        "operating_system": "rhel8",
                        "target": "aarch64",
                        "environment": {
                            "set": {
                                "fcc_ENV": "-Nclang",
                                "FCC_ENV": "-Nclang",
                            },
                            "prepend_path": {
                                "PATH": "/opt/FJSVxtclanga/tcsds-1.2.38/bin",
                                "LD_LIBRARY_PATH": "/opt/FJSVxtclanga/tcsds-1.2.38/lib64",
                            },
                        },
                        "extra_rpaths": [],
                    }
                }
            ]

        return selections

    def system_specific_variables(self):
        return {
            "extra_cmd_opts": "-std-proc fjmpioutdir/bmexe\n",
            "extra_batch_opts": '-x PJM_LLIO_GFSCACHE="/vol0002:/vol0003:/vol0004:/vol0005:/vol0006"\n',
            "post_exec_cmds": "for F in $(ls -1v fjmpioutdir/bmexe.*); do cat $F >> {log_file}; done\n",
        }

    def compute_software_section(self):
        return {
            "software": {
                "packages": {
                    "default-compiler": {
                        "pkg_spec": f"{self.spec.variants['compiler'][0]}"
                    },
                    "default-mpi": {"pkg_spec": "fujitsu-mpi"},
                    "compiler-clang": {"pkg_spec": "clang"},
                    "compiler-fj": {"pkg_spec": "fj"},
                    "compiler-gcc": {"pkg_spec": "gcc"},
                    "blas": {"pkg_spec": "fujitsu-ssl2"},
                    "lapack": {"pkg_spec": "fujitsu-ssl2"},
                }
            }
        }
