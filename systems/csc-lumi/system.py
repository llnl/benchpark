# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from packaging.version import Version

from benchpark.directives import maintainers, variant
from benchpark.paths import hardware_descriptions
from benchpark.rocmsystem import ROCmSystem
from benchpark.system import System, compiler_def, compiler_section_for, merge_dicts


class CscLumi(System):

    maintainers("mckinsey1")

    id_to_resources = {
        "lumi": {
            "rocm_arch": "gfx90a",
            "gtl_flag": "",
            "sys_cores_per_node": 64,
            "sys_gpus_per_node": 8,
            "sys_mem_per_node_GB": 512,
            "system_site": "csc",
            "scheduler": "slurm",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-zen3-MI250X-Slingshot/hardware_description.yaml",
        }
    }

    variant(
        "rocm",
        default="5.6.1",
        description="ROCm version",
    )
    variant(
        "gtl",
        default=False,
        values=(True, False),
        description="Use GTL-enabled MPI",
    )
    variant(
        "compiler",
        default="cce15",
        values=("gcc11", "gcc12", "cce14", "cce15", "cce16"),
        description="Which compiler to use",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [ROCmSystem()]
        self.rocm_version = Version(self.spec.variants["rocm"][0])
        self.gtl_flag = self.spec.variants["gtl"][0]

        full_versions = {
            "cce16": "16.0.1",
            "cce15": "15.0.1",
            "cce14": "14.0.2",
            "gcc12": "12.2.0",
            "gcc11": "11.2.0",
        }
        for key, value in full_versions.items():
            if key == self.spec.variants["compiler"][0]:
                self.compiler_version = Version(value)

        attrs = self.id_to_resources.get("lumi")
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):

        selections = {
            "packages": {
                "mpi": {"buildable": False},
                "cray-mpich": {
                    "externals": [
                        {
                            "spec": "cray-mpich@8.1.27%gcc",
                            "prefix": "/opt/cray/pe/mpich/8.1.27/ofi/gnu/9.1",
                            "modules": ["libfabric/1.15.2.0"],
                        },
                        {
                            "spec": "cray-mpich@8.1.27%cce",
                            "prefix": "/opt/cray/pe/mpich/8.1.27/ofi/cray/14.0",
                            "modules": ["libfabric/1.15.2.0"],
                        },
                        {
                            "spec": "cray-mpich@8.1.27%rocmcc",
                            "prefix": "/opt/cray/pe/mpich/8.1.27/ofi/amd/5.0",
                            "modules": ["libfabric/1.15.2.0"],
                        },
                    ],
                    "buildable": False,
                },
                "blas": {"buildable": False},
                "lapack": {"buildable": False},
                "cray-libsci": {
                    "externals": [
                        {
                            "spec": "cray-libsci@23.09.1.1%rocmcc",
                            "prefix": "/opt/cray/pe/libsci/23.09.1.1/AMD/5.0/x86_64",
                            "modules": ["cray-libsci/23.09.1.1"],
                        }
                    ],
                    "buildable": False,
                },
                "gcc": {
                    "externals": [
                        {
                            "spec": "gcc@7.5.0 languages=c,c++,fortran",
                            "prefix": "/usr",
                            "extra_attributes": {
                                "compilers": {
                                    "c": "/usr/bin/gcc",
                                    "cxx": "/usr/bin/g++-7",
                                    "fortran": "/usr/bin/gfortran",
                                }
                            },
                        }
                    ]
                },
                "slurm": {
                    "externals": [{"spec": "slurm@22.05.10", "prefix": "/usr"}],
                    "buildable": False,
                },
            }
        }

        selections["packages"] |= self.rocm_config()["packages"]

        if self.spec.satisfies("compiler=cce"):
            selections |= {
                "packages": selections["packages"]
                | {
                    "cray-libsci": {
                        "externals": [
                            {
                                "spec": "cray-libsci@23.09.1.1%cce",
                                "prefix": "/opt/cray/pe/libsci/23.09.1.1/cray/12.0/x86_64",
                                "modules": ["cray-libsci/23.09.1.1"],
                            }
                        ]
                    }
                }
            }
        elif self.spec.satisfies("compiler=gcc"):
            selections |= {
                "packages": selections["packages"]
                | {
                    "cray-libsci": {
                        "externals": [
                            {
                                "spec": "cray-libsci@23.09.1.1%gcc",
                                "prefix": "/opt/cray/pe/libsci/23.09.1.1/gnu/10.3/x86_64",
                            }
                        ]
                    }
                }
            }
        return selections

    def compute_compilers_section(self):
        chosen = [self.rocmcc_cfg()]
        if "cce" in self.spec.variants["compiler"][0]:
            chosen.append(self.cce_compiler_cfg())
        else:
            chosen.append(self.gcc_compiler_cfg())

        return merge_dicts(*chosen)

    def rocmcc_cfg(self):
        return compiler_section_for(
            "llvm-amdgpu",
            [
                compiler_def(
                    f"llvm-amdgpu@{self.rocm_version}",
                    f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/",
                    {"c": "amdclang", "cxx": "amdclang++", "fortran": "amdflang"},
                    env={
                        "set": {"RFE_811452_DISABLE": "1"},
                        "append_path": {"LD_LIBRARY_PATH": "/opt/cray/pe/gcc-libs"},
                        "prepend_path": {
                            "LD_LIBRARY_PATH": "/opt/cray/pe/pmi/6.1.12/lib",
                            "LIBRARY_PATH": f"/appl/lumi/SW/CrayEnv/EB/rocm/5.6.1/lib:/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/lib64",
                        },
                    },
                    extra_rpaths=[
                        f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/lib",
                        f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/lib64",
                        "/opt/cray/pe/gcc-libs",
                    ],
                )
            ],
        )

    def cce_compiler_cfg(self):
        return compiler_section_for(
            "cce",
            [
                compiler_def(
                    f"cce@{self.compiler_version}",
                    f"/opt/cray/pe/cce/{self.compiler_version}/",
                    {"c": "craycc", "cxx": "crayCC", "fortran": "crayftn"},
                    env={
                        "set": {"RFE_811452_DISABLE": "1"},
                        "prepend_path": {
                            "LD_LIBRARY_PATH": "/opt/cray/pe/pmi/6.1.12/lib"
                        },
                        "append_path": {
                            "LD_LIBRARY_PATH": "/opt/cray/pe/gcc-libs",
                            "PKG_CONFIG_PATH": "/usr/lib64/pkgconfig",
                        },
                    },
                    extra_rpaths=["/opt/cray/pe/gcc-libs"],
                )
            ],
        )

    def gcc_compiler_cfg(self):
        return compiler_section_for(
            "gcc",
            [
                compiler_def(
                    f"gcc@{self.compiler_version} languages:=c,c++,fortran",
                    f"/opt/cray/pe/gcc/{self.compiler_version}/",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                    env={
                        "prepend_path": {
                            "LD_LIBRARY_PATH": "/opt/cray/pe/pmi/6.1.12/lib:/opt/cray/libfabric/1.15.2.0/lib64",
                            "PKG_CONFIG_PATH": "/usr/lib64/pkgconfig",
                        }
                    },
                )
            ],
        )

    def rocm_config(self):
        return {
            "packages": {
                "comgr": {
                    "buildable": False,
                    "externals": [
                        {
                            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                            "spec": f"comgr@{self.rocm_version}",
                        }
                    ],
                },
                "hip": {
                    "buildable": False,
                    "externals": [
                        {
                            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/hip",
                            "spec": f"hip@{self.rocm_version}",
                        }
                    ],
                },
                "hip-rocclr": {
                    "buildable": False,
                    "externals": [
                        {
                            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/rocclr",
                            "spec": f"hip-rocclr@{self.rocm_version}",
                        }
                    ],
                },
                "hipblas": {
                    "buildable": False,
                    "externals": [
                        {
                            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                            "spec": f"hipblas@{self.rocm_version}",
                        }
                    ],
                },
                "hipcub": {
                    "buildable": False,
                    "externals": [
                        {
                            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                            "spec": f"hipcub@{self.rocm_version}",
                        }
                    ],
                },
                "hipfft": {
                    "buildable": False,
                    "externals": [
                        {
                            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                            "spec": f"hipfft@{self.rocm_version}",
                        }
                    ],
                },
                "hipfort": {
                    "buildable": False,
                    "externals": [
                        {
                            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                            "spec": f"hipfort@{self.rocm_version}",
                        }
                    ],
                },
                "hipify-clang": {
                    "buildable": False,
                    "externals": [
                        {
                            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                            "spec": f"hipify-clang@{self.rocm_version}",
                        }
                    ],
                },
                "hipsparse": {
                    "buildable": False,
                    "externals": [
                        {
                            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                            "spec": f"hipsparse@{self.rocm_version}",
                        }
                    ],
                },
                "hsa-rocr-dev": {
                    "buildable": False,
                    "externals": [
                        {
                            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                            "spec": f"hsa-rocr-dev@{self.rocm_version}",
                        }
                    ],
                },
                "hsakmt-roct": {
                    "buildable": False,
                    "externals": [
                        {
                            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                            "spec": f"hsakmt-roct@{self.rocm_version}",
                        }
                    ],
                },
                # "llvm-amdgpu": {
                #    "buildable": False,
                #    "externals": [
                #        {
                #            "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/llvm",
                #            "spec": f"llvm-amdgpu@{self.rocm_version}",
                #        }
                #    ],
            },
            "rccl": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rccl@{self.rocm_version}",
                    }
                ],
            },
            "rocalution": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocalution@{self.rocm_version}",
                    }
                ],
            },
            "rocblas": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocblas@{self.rocm_version}",
                    }
                ],
            },
            "rocfft": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocfft@{self.rocm_version}",
                    }
                ],
                "variants": "amdgpu_target=auto amdgpu_target_sram_ecc=auto",
            },
            "rocm-clang-ocl": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocm-clang-ocl@{self.rocm_version}",
                    }
                ],
            },
            "rocm-cmake": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocm-cmake@{self.rocm_version}",
                    }
                ],
            },
            "rocm-device-libs": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocm-device-libs@{self.rocm_version}",
                    }
                ],
            },
            "rocm-gdb": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocm-gdb@{self.rocm_version}",
                    }
                ],
            },
            "rocm-opencl": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/opencl",
                        "spec": f"rocm-opencl@{self.rocm_version}",
                    }
                ],
            },
            "rocm-opencl-runtime": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/opencl",
                        "spec": f"rocm-opencl-runtime@{self.rocm_version}",
                    }
                ],
            },
            "rocm-openmp-extras": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/llvm",
                        "spec": f"rocm-openmp-extras@{self.rocm_version}",
                    }
                ],
            },
            "rocm-smi": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/rocm_smi",
                        "spec": f"rocmsmi@{self.rocm_version}",
                    }
                ],
            },
            "rocm-smi-lib": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/rocm_smi",
                        "spec": f"rocm-smi-lib@{self.rocm_version}",
                    }
                ],
            },
            "rocminfo": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocminfo@{self.rocm_version}",
                    }
                ],
            },
            "rocprim": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocprim@{self.rocm_version}",
                    }
                ],
            },
            "rocprofiler-dev": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocprofiler-dev@{self.rocm_version}",
                    }
                ],
            },
            "rocrand": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocrand@{self.rocm_version}",
                    }
                ],
            },
            "rocsolver": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocsolver@{self.rocm_version}",
                    }
                ],
            },
            "rocsparse": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocsparse@{self.rocm_version}",
                    }
                ],
            },
            "rocthrust": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"rocthrust@{self.rocm_version}",
                    }
                ],
            },
            "roctracer-dev": {
                "buildable": False,
                "externals": [
                    {
                        "prefix": f"/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}",
                        "spec": f"roctracer-dev@{self.rocm_version}",
                    }
                ],
            },
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
                    "default-mpi": {"pkg_spec": "cray-mpich@8.1~gtl %cce"},
                    "compiler-rocm": {
                        "pkg_spec": f"{self.spec.variants['compiler'][0]}"
                    },
                    "blas-rocm": {"pkg_spec": f"rocblas@{self.rocm_version}"},
                    "blas": {"pkg_spec": "cray-libsci@23"},
                    "lapack": {"pkg_spec": "cray-libsci@23"},
                    "mpi-rocm-gtl": {"pkg_spec": "cray-mpich@8.1+gtl %cce"},
                    "mpi-rocm-no-gtl": {"pkg_spec": "cray-mpich@8.1~gtl %cce"},
                    "mpi-gcc": {"pkg_spec": "cray-mpich@8.1~gtl %gcc"},
                }
            }
        }
