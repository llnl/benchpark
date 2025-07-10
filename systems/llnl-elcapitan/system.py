# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant, maintainers
from benchpark.paths import hardware_descriptions
from benchpark.rocmsystem import ROCmSystem
from benchpark.system import System
from packaging.version import Version


class LlnlElcapitan(System):

    maintainers("pearce8", "nhanford", "rfhaque")

    id_to_resources = {
        "tioga": {
            "rocm_arch": "gfx90a",
            "sys_cores_per_node": 56,
            "sys_cores_os_reserved_per_node": 8,
            "sys_cores_os_reserved_per_node_list": [0, 8, 16, 24, 32, 40, 48, 56],
            "sys_gpus_per_node": 8,
            "system_site": "llnl",
            "scheduler": "flux",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-zen3-MI250X-Slingshot/hardware_description.yaml",
        },
        "elcapitan": {
            "rocm_arch": "gfx942",
            "sys_cores_per_node": 84,
            "sys_cores_os_reserved_per_node": 12,
            "sys_cores_os_reserved_per_node_list": [
                0,
                8,
                16,
                24,
                32,
                40,
                48,
                56,
                64,
                72,
                80,
                88,
            ],  # 3 cores reserved per socket
            "sys_gpus_per_node": None,  # Determined by "gpumode" variant
            "system_site": "llnl",
            "scheduler": "flux",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-zen4-MI300A-Slingshot/hardware_description.yaml",
        },
    }
    id_to_resources["tuolumne"] = id_to_resources["elcapitan"]

    variant(
        "cluster",
        default="tioga",
        values=("tioga", "elcapitan", "tuolumne"),
        description="Which cluster to run on",
    )
    variant(
        "gpumode",
        default="SPX",
        values=("SPX", "TPX", "CPX"),
        description="compute partitioning modes for MI300A",
    )
    variant(
        "rocm",
        default="6.2.4",
        values=("5.7.1", "6.2.4", "6.3.1"),
        description="ROCm version",
    )
    variant(
        "gtl",
        default=True,
        values=(True, False),
        description="Use GTL-enabled MPI",
    )
    variant(
        "compiler",
        default="cce",
        values=("cce", "gcc", "rocmcc"),
        description="Which compiler to use",
    )
    variant(
        "lapack",
        default="intel-oneapi-mkl",
        values=("intel-oneapi-mkl", "cray-libsci"),
        description="Which lapack to use",
    )
    variant(
        "blas",
        default="intel-oneapi-mkl",
        values=("intel-oneapi-mkl",),
        description="Which blas to use",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [ROCmSystem()]
        self.rocm_version = Version(self.spec.variants["rocm"][0])
        self.gtl_flag = self.spec.variants["gtl"][0]

        # TODO: Replace this with lookups into the working set
        if self.spec.satisfies("compiler=gcc"):
            self.gcc_version = Version("12.2.0")
            self.mpi_version = Version("8.1.26")
        else:
            if self.rocm_version >= Version("6.0.0"):
                self.cce_version = Version("18.0.1")
                self.mpi_version = Version("8.1.31")
            else:
                self.cce_version = Version("16.0.0")
                self.mpi_version = Version("8.1.26")
            self.short_cce_version = (
                f"{self.cce_version.major}.{self.cce_version.minor}"
            )
        if self.rocm_version >= Version("6.0.0"):
            self.pmi_version = Version("6.1.15.6")
            self.pals_version = Version("1.2.12")
            self.llvm_version = Version("18.0.1")
        else:
            self.pmi_version = Version("6.1.12")
            self.pals_version = Version("1.2.9")
            self.llvm_version = Version("16.0.0")
        # TODO: Replace this with lookups into the working set

        attrs = self.id_to_resources.get(self.spec.variants["cluster"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

        # MI300A modes
        if self.rocm_arch == "gfx942":
            if self.spec.satisfies("gpumode=SPX"):
                self.sys_gpus_per_node = 4
            elif self.spec.satisfies("gpumode=TPX"):
                self.sys_gpus_per_node = 12
            elif self.spec.satisfies("gpumode=CPX"):
                self.sys_gpus_per_node = 24
            else:
                raise ValueError(f"Invalid gpumode in spec: {self.spec}")

    def compute_packages_section(self):
        selections = {
            "packages": {
                "all": {"require": "target=x86_64:"},
                "tar": {"externals": [{"spec": "tar@1.30", "prefix": "/usr"}]},
                "coreutils": {
                    "externals": [{"spec": "coreutils@8.30", "prefix": "/usr"}]
                },
                "libtool": {"externals": [{"spec": "libtool@2.4.6", "prefix": "/usr"}]},
                "flex": {"externals": [{"spec": "flex@2.6.1+lex", "prefix": "/usr"}]},
                "openssl": {
                    "externals": [{"spec": "openssl@1.1.1k", "prefix": "/usr"}]
                },
                "m4": {"externals": [{"spec": "m4@1.4.18", "prefix": "/usr"}]},
                "groff": {"externals": [{"spec": "groff@1.22.3", "prefix": "/usr"}]},
                "cmake": {
                    "externals": [
                        {"spec": "cmake@3.20.2", "prefix": "/usr"},
                        {"spec": "cmake@3.23.1", "prefix": "/usr/tce"},
                        {"spec": "cmake@3.24.2", "prefix": "/usr/tce"},
                    ],
                    "buildable": False,
                },
                "elfutils": {
                    "externals": [{"spec": "elfutils@0.190", "prefix": "/usr"}],
                    "buildable": False,
                },
                "papi": {
                    "externals": [{"spec": "papi@5.6.0.0", "prefix": "/usr"}],
                    "buildable": False,
                },
                "unwind": {
                    "externals": [{"spec": "unwind@8.0.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "pkgconf": {"externals": [{"spec": "pkgconf@1.4.2", "prefix": "/usr"}]},
                "curl": {
                    "externals": [
                        {"spec": "curl@7.61.1+gssapi+ldap+nghttp2", "prefix": "/usr"}
                    ]
                },
                "gmake": {"externals": [{"spec": "gmake@4.2.1", "prefix": "/usr"}]},
                "subversion": {
                    "externals": [{"spec": "subversion@1.10.2", "prefix": "/usr"}]
                },
                "diffutils": {
                    "externals": [{"spec": "diffutils@3.6", "prefix": "/usr"}]
                },
                "swig": {"externals": [{"spec": "swig@3.0.12", "prefix": "/usr"}]},
                "gawk": {"externals": [{"spec": "gawk@4.2.1", "prefix": "/usr"}]},
                "binutils": {
                    "externals": [{"spec": "binutils@2.30.113", "prefix": "/usr"}]
                },
                "findutils": {
                    "externals": [{"spec": "findutils@4.6.0", "prefix": "/usr"}]
                },
                "git-lfs": {
                    "externals": [{"spec": "git-lfs@2.11.0", "prefix": "/usr/tce"}]
                },
                "ccache": {"externals": [{"spec": "ccache@3.7.7", "prefix": "/usr"}]},
                "automake": {
                    "externals": [{"spec": "automake@1.16.1", "prefix": "/usr"}]
                },
                "cvs": {"externals": [{"spec": "cvs@1.11.23", "prefix": "/usr"}]},
                "git": {
                    "externals": [
                        {"spec": "git@2.31.1+tcltk", "prefix": "/usr"},
                        {"spec": "git@2.29.1+tcltk", "prefix": "/usr/tce"},
                    ]
                },
                "openssh": {"externals": [{"spec": "openssh@8.0p1", "prefix": "/usr"}]},
                "autoconf": {
                    "externals": [{"spec": "autoconf@2.69", "prefix": "/usr"}]
                },
                "texinfo": {"externals": [{"spec": "texinfo@6.5", "prefix": "/usr"}]},
                "bison": {"externals": [{"spec": "bison@3.0.4", "prefix": "/usr"}]},
                "python": {
                    "externals": [
                        {
                            "spec": "python@3.9.12",
                            "prefix": "/usr/tce/packages/python/python-3.9.12",
                            "buildable": False,
                        }
                    ]
                },
                "unzip": {
                    "buildable": False,
                    "externals": [{"spec": "unzip@6.0", "prefix": "/usr"}],
                },
                "hypre": {"variants": f"amdgpu_target={self.rocm_arch}"},
                "hwloc": {
                    "externals": [
                        {"spec": "hwloc@2.9.1", "prefix": "/usr", "buildable": False}
                    ]
                },
                "fftw": {"buildable": False},
                "intel-oneapi-mkl": {
                    "externals": [
                        {
                            "spec": "intel-oneapi-mkl@2023.2.0",
                            "prefix": "/opt/intel/oneapi",
                        }
                    ],
                    "buildable": False,
                },
                "fftw-api": {
                    "buildable": False,
                    "require": "intel-oneapi-mkl",
                },
                "mpi": {"buildable": False},
                "libfabric": {
                    "externals": [
                        {"spec": "libfabric@2.1", "prefix": "/opt/cray/libfabric/2.1"}
                    ],
                    "buildable": False,
                },
            }
        }

        selections["packages"] |= self.rocm_config()["packages"]

        selections["packages"] |= self.mpi_config()["packages"]

        if self.spec.satisfies("compiler=cce"):
            selections["packages"] |= {
                "cray-libsci": {
                    "externals": [
                        {
                            "spec": "cray-libsci@23.05.1.4%cce",
                            "prefix": "/opt/cray/pe/libsci/23.05.1.4/cray/12.0/x86_64/",
                        }
                    ]
                }
            }
        elif self.spec.satisfies("compiler=gcc"):
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

        if compiler == "cce":
            return {"packages": {"all": {"require": [{"one_of": ["%cce", "%gcc"]}]}}}
        elif compiler == "gcc":
            return {"packages": {}}
        elif compiler == "rocmcc":
            return {"packages": {"all": {"require": [{"one_of": ["%rocmcc", "%gcc"]}]}}}
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
        if self.spec.satisfies("compiler=cce") or self.spec.satisfies(
            "compiler=rocmcc"
        ):
            selections["compilers"] += self.rocm_cce_compiler_cfg()["compilers"]

        # Note: this is always included for some low-level dependencies
        # that shouldn't build with %cce

        return selections

    def mpi_config(self):
        gtl = self.spec.variants["gtl"][0]

        if self.spec.satisfies("compiler=cce"):
            dont_use_gtl = {
                "gtl_lib_path": f"/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
                "ldflags": f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
            }

            use_gtl = {
                "gtl_flags": "$MV2_COMM_WORLD_LOCAL_RANK",
                "gtl_cutoff_size": "4096",
                "fi_cxi_ats": "0",
                "gtl_lib_path": f"/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
                "gtl_libs": "libmpi_gtl_hsa",
                "ldflags": f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -lmpi_gtl_hsa",
            }

            if gtl:
                gtl_spec = "+gtl"
                gtl_cfg = use_gtl
            else:
                gtl_spec = "~gtl"
                gtl_cfg = dont_use_gtl

            return {
                "packages": {
                    "cray-mpich": {
                        "externals": [
                            {
                                "spec": f"cray-mpich@{self.mpi_version}{gtl_spec}+wrappers %cce@{self.cce_version}",
                                "prefix": f"/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}",
                                "extra_attributes": gtl_cfg,  # Assuming `gtl_cfg` is already defined elsewhere
                            }
                        ]
                    }
                }
            }
        elif self.spec.satisfies("compiler=rocmcc"):
            dont_use_gtl = {
                "gtl_lib_path": f"/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
                "ldflags": f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}/lib -lmpi "
                f"-L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib "
                f"-Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
            }

            use_gtl = {
                "gtl_cutoff_size": "4096",
                "fi_cxi_ats": "0",
                "gtl_lib_path": f"/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
                "gtl_libs": "libmpi_gtl_hsa",
                "ldflags": f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}/lib -lmpi "
                f"-L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib "
                f"-Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -lmpi_gtl_hsa",
            }

            if gtl:
                gtl_spec = "+gtl"
                gtl_cfg = use_gtl
            else:
                gtl_spec = "~gtl"
                gtl_cfg = dont_use_gtl

            return {
                "packages": {
                    "cray-mpich": {
                        "externals": [
                            {
                                "spec": f"cray-mpich@{self.mpi_version}{gtl_spec}+wrappers %cce@{self.cce_version}",
                                "prefix": f"/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}",
                                "extra_attributes": gtl_cfg,
                            }
                        ]
                    }
                }
            }

        elif self.spec.satisfies("compiler=gcc"):
            return {
                "packages": {
                    "cray-mpich": {
                        "externals": [
                            {
                                "spec": f"cray-mpich@{self.mpi_version}~gtl+wrappers %gcc@{self.gcc_version}",
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

    def rocm_config(self):
        return {
            "packages": {
                "blas": {"require": [f"{self.spec.variants['blas'][0]}"]},
                "lapack": {"require": [f"{self.spec.variants['lapack'][0]}"]},
                "hipfft": {
                    "externals": [
                        {
                            "spec": f"hipfft@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
                "rocfft": {
                    "externals": [
                        {
                            "spec": f"rocfft@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
                "rocprim": {
                    "externals": [
                        {
                            "spec": f"rocprim@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
                "rocrand": {
                    "externals": [
                        {
                            "spec": f"rocrand@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
                "rocsparse": {
                    "externals": [
                        {
                            "spec": f"rocsparse@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
                "rocthrust": {
                    "externals": [
                        {
                            "spec": f"rocthrust@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
                "hip": {
                    "externals": [
                        {
                            "spec": f"hip@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
                "hsa-rocr-dev": {
                    "externals": [
                        {
                            "spec": f"hsa-rocr-dev@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
                "comgr": {
                    "externals": [
                        {
                            "spec": f"comgr@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}/",
                        }
                    ],
                    "buildable": False,
                },
                "hiprand": {
                    "externals": [
                        {
                            "spec": f"hiprand@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
                "hipsparse": {
                    "externals": [
                        {
                            "spec": f"hipsparse@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
                "hipblas": {
                    "externals": [
                        {
                            "spec": f"hipblas@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}/",
                        }
                    ],
                    "buildable": False,
                },
                "hipsolver": {
                    "externals": [
                        {
                            "spec": f"hipsolver@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}/",
                        }
                    ],
                    "buildable": False,
                },
                "hsakmt-roct": {
                    "externals": [
                        {
                            "spec": f"hsakmt-roct@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}/",
                        }
                    ],
                    "buildable": False,
                },
                "roctracer-dev-api": {
                    "externals": [
                        {
                            "spec": f"roctracer-dev-api@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}/",
                        }
                    ],
                    "buildable": False,
                },
                "rocminfo": {
                    "externals": [
                        {
                            "spec": f"rocminfo@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}/",
                        }
                    ],
                    "buildable": False,
                },
                "llvm": {
                    "externals": [
                        {
                            "spec": f"llvm@{self.llvm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}/llvm",
                        }
                    ],
                    "buildable": False,
                },
                "llvm-amdgpu": {
                    "externals": [
                        {
                            "spec": f"llvm-amdgpu@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}/llvm",
                        }
                    ],
                    "buildable": False,
                },
                "rocblas": {
                    "externals": [
                        {
                            "spec": f"rocblas@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
                "rocsolver": {
                    "externals": [
                        {
                            "spec": f"rocsolver@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ],
                    "buildable": False,
                },
            }
        }

    def rocm_cce_compiler_cfg(self):
        if self.spec.satisfies("compiler=rocmcc"):
            return {
                "compilers": [
                    {
                        "compiler": {
                            "spec": f"rocmcc@{self.rocm_version}",
                            "paths": {
                                "cc": f"/opt/rocm-{self.rocm_version}/bin/amdclang",
                                "cxx": f"/opt/rocm-{self.rocm_version}/bin/amdclang++",
                                "f77": f"/opt/rocm-{self.rocm_version}/bin/amdflang",
                                "fc": f"/opt/rocm-{self.rocm_version}/bin/amdflang",
                            },
                            "flags": {"cflags": "-g -O2", "cxxflags": "-g -O2"},
                            "operating_system": "rhel8",
                            "target": "x86_64",
                            "modules": [f"cce/{self.cce_version}"],
                            "environment": {
                                "set": {"RFE_811452_DISABLE": "1"},
                                "append_path": {
                                    "LD_LIBRARY_PATH": "/opt/cray/pe/gcc-libs"
                                },
                                "prepend_path": {
                                    "LD_LIBRARY_PATH": f"/opt/cray/pe/cce/{self.cce_version}/cce/x86_64/lib:/opt/cray/pe/pmi/{self.pmi_version}/lib:/opt/cray/pe/pals/{self.pals_version}/lib",
                                    "LIBRARY_PATH": f"/opt/rocm-{self.rocm_version}/lib",
                                },
                            },
                            "extra_rpaths": [
                                f"/opt/rocm-{self.rocm_version}/lib",
                                "/opt/cray/pe/gcc-libs",
                                f"/opt/cray/pe/cce/{self.cce_version}/cce/x86_64/lib",
                            ],
                        }
                    }
                ]
            }
        else:
            return {
                "compilers": [
                    {
                        "compiler": {
                            "spec": f"cce@{self.cce_version}-rocm{self.rocm_version}",
                            "paths": {
                                "cc": f"/opt/cray/pe/cce/{self.cce_version}/bin/craycc",
                                "cxx": f"/opt/cray/pe/cce/{self.cce_version}/bin/crayCC",
                                "f77": f"/opt/cray/pe/cce/{self.cce_version}/bin/crayftn",
                                "fc": f"/opt/cray/pe/cce/{self.cce_version}/bin/crayftn",
                            },
                            "flags": {
                                "cflags": "-g -O2",
                                "cxxflags": "-g -O2 -std=c++14",
                                "fflags": "-g -O2 -hnopattern",
                                "ldflags": "-ldl",
                            },
                            "operating_system": "rhel8",
                            "target": "x86_64",
                            "modules": [f"cce/{self.cce_version}"],
                            "environment": {
                                "prepend_path": {
                                    "LD_LIBRARY_PATH": f"/opt/cray/pe/cce/{self.cce_version}/cce/x86_64/lib:/opt/rocm-{self.rocm_version}/lib:/opt/cray/pe/pmi/{self.pmi_version}/lib:/opt/cray/pe/pals/{self.pals_version}/lib"
                                }
                            },
                            "extra_rpaths": [
                                f"/opt/cray/pe/cce/{self.cce_version}/cce/x86_64/lib/",
                                "/opt/cray/pe/gcc-libs/",
                                f"/opt/rocm-{self.rocm_version}/lib",
                            ],
                        }
                    }
                ]
            }

    def system_specific_variables(self):
        opts = super().system_specific_variables()
        # MI300A modes
        if self.rocm_arch == "gfx942":
            if self.spec.satisfies("gpumode=SPX"):
                gpu_factor = 1
            elif self.spec.satisfies("gpumode=TPX"):
                gpu_factor = 3
            elif self.spec.satisfies("gpumode=CPX"):
                gpu_factor = 6

            opts.update(
                {
                    "gpu_factor": gpu_factor,
                    "extra_batch_opts": f"--setattr=gpumode={self.spec.variants['gpumode'][0]}\n--conf=resource.rediscover=true",
                }
            )
        return opts

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
                    "compiler-rocm": {"pkg_spec": "cce"},
                    "compiler-amdclang": {"pkg_spec": "clang"},
                    "compiler-gcc": {"pkg_spec": "gcc"},
                    "mpi-rocm-gtl": {"pkg_spec": "cray-mpich+gtl"},
                    "mpi-rocm-no-gtl": {"pkg_spec": "cray-mpich~gtl"},
                    "mpi-gcc": {"pkg_spec": "cray-mpich~gtl"},
                    "blas": {"pkg_spec": f"{self.spec.variants['blas'][0]}"},
                    "blas-rocm": {"pkg_spec": "rocblas"},
                    "lapack": {"pkg_spec": f"{self.spec.variants['lapack'][0]}"},
                    "lapack-oneapi": {"pkg_spec": "intel-oneapi-mkl"},
                    "lapack-rocm": {"pkg_spec": "rocsolver"},
                }
            }
        }
