# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from packaging.version import Version

from benchpark.directives import variant, maintainers
from benchpark.system import System
from benchpark.paths import hardware_descriptions


class LbnlPerlmutter(System):

    maintainers("slabasan")

    id_to_resources = {
        "perlmutter": {
            "cuda_arch": "80",
            "sys_cores_per_node": 64,
            "sys_gpus_per_node": 4,
            "system_site": "lbnl",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-zen3-A100-Slingshot/hardware_description.yaml",
        },
    }

    variant(
        "compiler",
        default="gcc",
        values=("gcc"),
        description="Which compiler to use",
    )

    def __init__(self, spec):
        super().__init__(spec)

        if self.spec.satisfies("compiler=gcc"):
            self.gcc_version = Version("13.2.1")
            self.mpi_version = Version("8.1.30")

        self.scheduler = "slurm"
        attrs = self.id_to_resources.get("perlmutter")
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):
        selections = {
            "packages": {
                "all": {"require": "target=x86_64:"},
                "tar": {"externals": [{"spec": "tar@1.34", "prefix": "/usr"}]},
                "coreutils": {
                    "externals": [{"spec": "coreutils@8.32", "prefix": "/usr"}]
                },
                "libtool": {"externals": [{"spec": "libtool@2.4.6", "prefix": "/usr"}]},
                "flex": {"externals": [{"spec": "flex@2.6.4+lex", "prefix": "/usr"}]},
                "openssl": {
                    "externals": [{"spec": "openssl@1.1.1l-fips", "prefix": "/usr"}]
                },
                "m4": {"externals": [{"spec": "m4@1.4.18", "prefix": "/usr"}]},
                "groff": {"externals": [{"spec": "groff@1.22.4", "prefix": "/usr"}]},
                "cmake": {
                    "externals": [{"spec": "cmake@3.20.4", "prefix": "/usr"}],
                    "buildable": False,
                },
                "curl": {
                    "externals": [
                        {"spec": "curl@8.0.1+gssapi+ldap+nghttp2", "prefix": "/usr"}
                    ]
                },
                "gmake": {"externals": [{"spec": "gmake@4.2.1", "prefix": "/usr"}]},
                "subversion": {
                    "externals": [{"spec": "subversion@1.14.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "diffutils": {
                    "externals": [{"spec": "diffutils@3.6", "prefix": "/usr"}],
                    "buildable": False,
                },
                "gawk": {"externals": [{"spec": "gawk@4.2.1", "prefix": "/usr"}]},
                "binutils": {
                    "externals": [
                        {"spec": "binutils@2.40~gold~headers", "prefix": "/opt/cray/pe/cce/18.0.0/binutils/x86_64/x86_64-pc-linux-gnu"}
                        {"spec": "binutils@2.43.1~gold~headers", "prefix": "/usr"}
                    ],
                    "buildable": False,
                },
                "findutils": {
                    "externals": [{"spec": "findutils@4.8.0", "prefix": "/usr"}],
                    "buildable": False,
                },
                "ccache": {
                    "externals": [{"spec": "ccache@3.4.7", "prefix": "/usr"}]},
                    "buildable": False,
                },
                "automake": {
                    "externals": [{"spec": "automake@1.15.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "git": {
                    "externals": [{"spec": "git@2.35.3~tcltk", "prefix": "/usr"}],
                    "buildable": False,
                },
                "openssh": {
                    "externals": [{"spec": "openssh@8.4p1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "autoconf": {
                    "externals": [{"spec": "autoconf@2.69", "prefix": "/usr"}],
                    "buildable": False,
                },
                "bison": {
                    "externals": [{"spec": "bison@3.0.4", "prefix": "/usr"}],
                    "buildable": False,
                },
                "python": {
                    "externals": [
                        {
                            "prefix": "/usr",
                            "spec": "python@2.7.18+bz2+crypt+ctypes~dbm~lzma+nis~pyexpat+pythoncmd~readline~sqlite3~ssl~tkinter+uuid+zlib",
                        },
                        {
                            "prefix": "/usr",
                            "spec": "python@3.6.15+bz2+crypt+ctypes~dbm+lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl~tkinter+uuid+zlib",
                        },
                    ],
                    "buildable": False,
                },
                "doxygen": {
                    "externals": [{"spec": "doxygen@1.8.14~graphviz~mscgen", "prefix": "/usr"}],
                    "buildable": False,
                },
                "gettext": {
                    "externals": [{"spec": "gettext@0.20.2", "prefix": "/usr"}],
                    "buildable": False,
                },
                "ninja": {
                    "externals": [{"spec": "ninja@1.10.0", "prefix": "/usr"}],
                    "buildable": False,
                },
                "perl": {
                    "externals": [{"spec": "perl@5.26.1~cpanm+opcode+open+shared+threads", "prefix": "/usr"}],
                    "buildable": False,
                },
                "pkg-config": {
                    "externals": [{"spec": "pkg-config@0.29.2", "prefix": "/usr"}],
                    "buildable": False,
                },
                "sed": {
                    "externals": [{"spec": "sed@4.4", "prefix": "/usr"}],
                    "buildable": False,
                },
                "tar": {
                    "externals": [{"spec": "tar@1.34", "prefix": "/usr"}],
                    "buildable": False,
                },
                "zlib": {
                    "externals": [{"spec": "zlib@1.2.13", "prefix": "/usr"}],
                    "buildable": False,
                },
            }

        selections["packages"] |= self.mpi_config()["packages"]

        if self.spec.satisfies("compiler=gcc"):
            selections["packages"] |= {
                "cray-libsci": {
                    "externals": [
                        {
                            "spec": "cray-libsci@23.05.1.4%gcc",
                            "prefix": "/opt/cray/pe/libsci/23.05.1.4/gnu/10.3/x86_64/",
                        }
                    ]
                }
            }

        selections["packages"] |= self.compiler_weighting_cfg()["packages"]

        return selections

    def compiler_weighting_cfg(self):
        compiler = self.spec.variants["compiler"][0]

        if compiler == "gcc":
            return {"packages": {}}
        else:
            raise ValueError(f"Unexpected value for compiler: {compiler}")

    def compute_compilers_section(self):
        selections = {
            "compilers": [
                {
                    "compiler": {
                        "spec": "gcc@12.2.0",
                        "paths": {
                            "cc": "/opt/cray/pe/gcc/12.2.0/bin/gcc",
                            "cxx": "/opt/cray/pe/gcc/12.2.0/bin/g++",
                            "f77": "/opt/cray/pe/gcc/12.2.0/bin/gfortran",
                            "fc": "/opt/cray/pe/gcc/12.2.0/bin/gfortran",
                        },
                        "flags": {},
                        "operating_system": "rhel8",
                        "target": "x86_64",
                        "modules": [],
                        "environment": {},
                        "extra_rpaths": [],
                    }
                }
            ]
        }

        return selections

    def mpi_config(self):
        gtl = self.spec.variants["gtl"][0]

        if self.spec.satisfies("compiler=gcc"):
            return {
                "packages": {
                    "cray-mpich": {
                        "externals": [
                            {
                                "spec": f"cray-mpich@{self.mpi_version}%gcc@{self.gcc_version} ~gtl +wrappers",
                                "prefix": f"/opt/cray/pe/mpich/{self.mpi_version}/ofi/gnu/10.3",
                                "extra_attributes": {
                                    "gtl_lib_path": f"/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
                                    "ldflags": f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/gnu/10.3/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
                                },
                            }
                        ]
                    }
                }
            }

    def compute_software_section(self):
        """This is somewhat vestigial: for the Tioga config that is committed
        to the repo, multiple instances of mpi/compilers are stored and
        and these variables were used to choose consistent dependencies.
        The configs generated by this class should only ever have one
        instance of MPI etc., so there is no need for that. The experiments
        will fail if these variables are not defined though, so for now
        they are still generated (but with more-generic values).
        """
        return {
            "software": {
                "packages": {
                    "default-compiler": {
                        "pkg_spec": f"{self.spec.variants['compiler'][0]}"
                    },
                    "default-mpi": {"pkg_spec": "cray-mpich"},
                    "compiler-amdclang": {"pkg_spec": "clang"},
                    "compiler-gcc": {"pkg_spec": "gcc"},
                    "mpi-gcc": {"pkg_spec": "cray-mpich~gtl"},
                    "blas": {"pkg_spec": f"{self.spec.variants['blas'][0]}"},
                    "lapack": {"pkg_spec": f"{self.spec.variants['lapack'][0]}"},
                    "lapack-oneapi": {"pkg_spec": "intel-oneapi-mkl"},
                }
            }
        }
