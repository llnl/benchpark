# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from packaging.version import Version

from benchpark.directives import maintainers, variant
from benchpark.paths import hardware_descriptions
from benchpark.rocmsystem import ROCmSystem
from benchpark.system import (
    System,
    compiler_def,
    compiler_section_for,
    merge_dicts,
)


class SnlEldorado(System):

    maintainers("simongdg", "pearce8", "nhanford", "rfhaque")

    id_to_resources = {
        "eldorado": {
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
            "sys_sockets_per_node": 4,
            "sys_mem_per_node_GB": 512,
            "sys_cpu_mem_per_node_MB": 3072,
            "sys_gpu_mem_per_node_GB": 512,
            "sys_gpu_num_L1": 228,
            "sys_gpu_L1_KB": 32,
            "sys_gpu_L2_KB": 4096,
            "sys_gpu_L3_MB": 256,
            "sys_cpu_L1_KB": 32,  # 32KB for L1d and 32KB for L1i
            "sys_cpu_L2_KB": 1024,  # 512 KB
            "sys_cpu_L3_MB": 32,  # 32MB
            "system_site": "snl",
            "scheduler": "flux",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-zen4-MI300A-Slingshot/hardware_description.yaml",
        }
    }
    variant(
        "gpumode",
        default="SPX",
        values=("SPX", "TPX", "CPX"),
        description="compute partitioning modes for MI300A",
    )
    variant(
        "rocm",
        default="6.4.0",
        values=("5.7.1", "6.2.4", "6.3.1", "6.4.0", "6.4.1", "6.4.2"),
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
        default="rocmcc",
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
            self.gcc_version = Version("12.2.1")
            self.mpi_version = Version("8.1.32")
        else:
            if self.rocm_version >= Version("6.4.0"):
                self.cce_version = Version("20.0.0")
                self.mpi_version = Version("9.0.1")
                self.short_cce_version = (
                    f"{self.cce_version.major}.{self.cce_version.minor}"
                )
            elif self.rocm_version >= Version("6.0.0"):
                self.cce_version = Version("18.0.1")
                self.mpi_version = Version("8.1.31")
                self.short_cce_version = (
                    f"{self.cce_version.major}.{self.cce_version.minor}"
                )
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

        for k, v in self.id_to_resources["eldorado"].items():
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
                "all": {"require": [{"spec": "target=x86_64:"}]},
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
                        }
                    ],
                    "buildable": False,
                },
                "unzip": {
                    "buildable": False,
                    "externals": [{"spec": "unzip@6.0", "prefix": "/usr"}],
                },
                "hypre": {"variants": f"amdgpu_target={self.rocm_arch}"},
                "hwloc": {
                    "externals": [{"spec": "hwloc@2.9.1", "prefix": "/usr"}],
                    "buildable": False,
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

            # Missing a line here if things fail

        return selections

    def compiler_weighting_cfg(self):
        compiler = self.spec.variants["compiler"][0]

        if compiler == "cce":
            prefs = {"one_of": ["%cce", "%gcc"], "when": "%c"}
            return {"packages": {"all": {"require": [prefs]}}}
        elif compiler == "gcc":
            return {"packages": {}}
        elif compiler == "rocmcc":
            prefs = {"one_of": ["%rocmcc", "%gcc"], "when": "%c"}
            return {"packages": {"all": {"require": [prefs]}}}
        else:
            raise ValueError(f"Unexpected value for compiler: {compiler}")

    def compute_compilers_section(self):
        cfg = compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@12.2.0 languages=c,c++,fortran",
                    "/opt/cray/pe/gcc/12.2.0/",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                )
            ],
        )

        if self.spec.satisfies("compiler=cce") or self.spec.satisfies(
            "compiler=rocmcc"
        ):
            cfg = merge_dicts(cfg, self.rocm_cce_compiler_cfg())

        return merge_dicts(cfg, self.compiler_weighting_cfg())

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
                "gtl_lib_path": f"/opt/cray/pe/mpich/{self.mpi_version}/ofi/amd/6.0/lib",
                "ldflags": f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/amd/6.0/lib -lmpi "
                f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/amd/6.0/lib "
                f"-Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/ofi/amd/6.0lib",
            }

            use_gtl = {
                "gtl_cutoff_size": "4096",
                "fi_cxi_ats": "0",
                "gtl_path": f"/opt/cray/pe/mpich/{self.mpi_version}/ofi/amd/6.0",
                "gtl_lib_path": f"/opt/cray/pe/mpich/{self.mpi_version}/ofi/amd/6.0/lib",
                "gtl_libs": "libmpi_gtl_hsa",
                "ldflags": f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/amd/6.0/lib -lmpi "
                f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/amd/6.0/lib "
                f"-Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/ofi/amd/6.0/lib -lmpi_gtl_hsa",
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
                                "spec": f"cray-mpich@{self.mpi_version}{gtl_spec}+wrappers%rocmcc@{self.rocm_version}",
                                "prefix": f"/opt/cray/pe/mpich/{self.mpi_version}/ofi/amd/6.0",
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
                                "spec": f"cray-mpich@{self.mpi_version}~gtl+wrappers%gcc@{self.gcc_version}",
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
                "rccl": {
                    "externals": [
                        {
                            "spec": f"rccl@{self.rocm_version}",
                            "prefix": f"/opt/rocm-{self.rocm_version}",
                        }
                    ]
                },
            }
        }

    def rocm_cce_compiler_cfg(self):
        rpaths = [
            f"/opt/rocm-{self.rocm_version}/lib",
            "/opt/cray/pe/gcc-libs",
            f"/opt/cray/pe/cce/{self.cce_version}/cce/x86_64/lib",
        ]

        cfgs = []
        # Always need an instance of llvm-gpu as an external. Sometimes as a compiler
        # and sometimes just for ROCm support
        rocmcc_entry = compiler_def(
            f"llvm-amdgpu@{self.rocm_version}",
            f"/opt/rocm-{self.rocm_version}/",
            {"c": "amdclang", "cxx": "amdclang++", "fortran": "amdflang"},
            modules=[f"cce/{self.cce_version}"],
            extra_rpaths=list(rpaths),
            env={
                "set": {"RFE_811452_DISABLE": "1"},
                "append_path": {"LD_LIBRARY_PATH": "/opt/cray/pe/gcc-libs"},
                "prepend_path": {
                    "LD_LIBRARY_PATH": f"/opt/cray/pe/cce/{self.cce_version}/cce/x86_64/lib:/opt/cray/pe/pmi/{self.pmi_version}/lib:/opt/cray/pe/pals/{self.pals_version}/lib",
                    "LIBRARY_PATH": f"/opt/rocm-{self.rocm_version}/lib",
                },
            },
        )
        cfgs.append(compiler_section_for("llvm-amdgpu", [rocmcc_entry]))
        if self.spec.satisfies("compiler=cce"):
            cce_entry = compiler_def(
                f"cce@{self.cce_version}-rocm{self.rocm_version}",
                f"/opt/cray/pe/cce/{self.cce_version}/",
                {"c": "craycc", "cxx": "crayCC", "fortran": "crayftn"},
                modules=[f"cce/{self.cce_version}"],
                extra_rpaths=list(rpaths),
                env={
                    "prepend_path": {
                        "LD_LIBRARY_PATH": f"/opt/cray/pe/cce/{self.cce_version}/cce/x86_64/lib:/opt/rocm-{self.rocm_version}/lib:/opt/cray/pe/pmi/{self.pmi_version}/lib:/opt/cray/pe/pals/{self.pals_version}/lib"
                    }
                },
            )
            cfgs.append(compiler_section_for("cce", [cce_entry]))
        return merge_dicts(*cfgs)

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
        default_compiler = "gcc"
        if self.spec.satisfies("compiler=cce"):
            default_compiler = "cce"
        elif self.spec.satisfies("compiler=rocmcc"):
            default_compiler = "llvm-amdgpu"

        return {
            "software": {
                "packages": {
                    "default-compiler": {"pkg_spec": default_compiler},
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
