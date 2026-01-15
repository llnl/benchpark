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
    JobQueue,
    System,
    compiler_def,
    compiler_section_for,
    hybrid_compiler_requirements,
    merge_dicts,
)


class LlnlSierra(System):

    maintainers("pearce8", "nhanford", "rfhaque")

    id_to_resources = {
        "lassen": {
            "cuda_arch": 70,
            "sys_cores_per_node": 40,
            "sys_sockets_per_node": 2,
            "sys_cores_os_reserved_per_node": 4,
            "sys_cores_os_reserved_per_node_list": [
                0,
                1,
                22,
                23,
            ],  # First two cores on each socket reserved.
            "sys_gpus_per_node": 4,
            "sys_mem_per_node_GB": 256,
            "sys_cpu_mem_per_node_MB": 40,
            "sys_gpu_mem_per_node_GB": 64,
            "sys_gpu_num_L1": 80,
            "sys_gpu_L1_KB": 128,
            "sys_gpu_L2_KB": 6144,
            "sys_cpu_L1_KB": 32,
            "sys_cpu_L2_KB": 512,
            "sys_cpu_L3_MB": 10,
            "system_site": "llnl",
            "hardware_key": str(hardware_descriptions)
            + "/IBM-power9-V100-Infiniband/hardware_description.yaml",
            "queues": [JobQueue("pdebug", 120, 18), JobQueue("pbatch", 720, 256)],
        },
    }
    id_to_resources["sierra"] = id_to_resources["lassen"]
    id_to_resources["sierra"]["queues"] = [
        JobQueue("pdebug", 120, 18),
        JobQueue("pbatch", 1440, 2048),
    ]

    variant(
        "cuda",
        default="11.8.0",
        values=("11.8.0", "10.1.243"),
        description="CUDA version",
    )
    variant(
        "gtl",
        default=False,
        values=(True, False),
        description="Use GTL-enabled MPI",
    )
    variant(
        "compiler",
        default="clang-ibm",
        values=("clang-ibm", "xl", "xl-gcc", "clang"),
        description="Which compiler to use",
    )
    variant(
        "lapack",
        default="essl",
        values=("essl",),
        description="Which lapack to use",
    )
    variant(
        "blas",
        default="essl",
        values=("essl",),
        description="Which blas to use",
    )

    variant(
        "bank",
        default="none",
        values=("none", "guests", "asccasc", "lc", "fractale"),
        multi=False,
        description="Submit a job to a specific named bank",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [CudaSystem(), OpenMPCPUOnlySystem()]
        self.cuda_version = Version(self.spec.variants["cuda"][0])
        self.gtl_flag = self.spec.variants["gtl"][0]

        self.scheduler = "lsf"
        attrs = self.id_to_resources.get("lassen")
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):

        selections = {
            "packages": {
                "elfutils": {
                    "externals": [{"spec": "elfutils@0.176", "prefix": "/usr"}],
                    "buildable": False,
                },
                "papi": {
                    "buildable": False,
                    "externals": [{"spec": "papi@5.2.0.0", "prefix": "/usr"}],
                },
                "unwind": {
                    "externals": [{"spec": "unwind@8.0.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "tar": {
                    "externals": [{"spec": "tar@1.26", "prefix": "/usr"}],
                    "buildable": False,
                },
                "cmake": {
                    "externals": [
                        {
                            "spec": "cmake@3.29.2",
                            "prefix": "/usr/tce/packages/cmake/cmake-3.29.2",
                        }
                    ],
                    "buildable": False,
                },
                "gmake": {
                    "externals": [
                        {
                            "spec": "gmake@4.2.1",
                            "prefix": "/usr/tcetmp/packages/gmake/gmake-4.2.1",
                        }
                    ],
                    "buildable": False,
                },
                "automake": {
                    "externals": [{"spec": "automake@1.13.4", "prefix": "/usr"}]
                },
                "autoconf": {
                    "externals": [{"spec": "autoconf@2.69", "prefix": "/usr"}]
                },
                "fftw": {
                    "externals": [
                        {
                            "spec": "fftw@3.3.10",
                            "prefix": "/usr/tcetmp/packages/fftw/fftw-3.3.10-xl-2023.06.28",
                        }
                    ],
                    "buildable": False,
                },
                "python": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "python@3.8.2",
                            "prefix": "/usr/tce/packages/python/python-3.8.2",
                        }
                    ],
                },
                "mpi": {"buildable": False},
            }
        }
        # 00-version-10-1-243-packages.yaml  01-version-11-8-0-packages.yaml
        if self.spec.satisfies("cuda=10.1.243"):
            selections["packages"] |= {
                "curand": {
                    "externals": [
                        {
                            "spec": "curand@10.1.243",
                            "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                        }
                    ],
                    "buildable": False,
                },
                "cusparse": {
                    "externals": [
                        {
                            "spec": "cusparse@10.1.243",
                            "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                        }
                    ],
                    "buildable": False,
                },
                "cuda": {
                    "externals": [
                        {
                            "spec": "cuda@10.1.243+allow-unsupported-compilers",
                            "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                        }
                    ],
                    "buildable": False,
                },
                "cub": {
                    "externals": [
                        {
                            "spec": "cub@10.1.243",
                            "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                        }
                    ],
                    "buildable": False,
                },
                "cublas": {
                    "externals": [
                        {
                            "spec": "cublas@10.1.243",
                            "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                        }
                    ],
                    "buildable": False,
                },
                "cusolver": {
                    "externals": [
                        {
                            "spec": "cusolver@10.1.243",
                            "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                        }
                    ],
                    "buildable": False,
                },
            }
        elif self.spec.satisfies("cuda=11.8.0"):
            selections["packages"] |= {
                "curand": {
                    "externals": [
                        {
                            "spec": "curand@11.8.0",
                            "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                        }
                    ],
                    "buildable": False,
                },
                "cusparse": {
                    "externals": [
                        {
                            "spec": "cusparse@11.8.0",
                            "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                        }
                    ],
                    "buildable": False,
                },
                "cuda": {
                    "externals": [
                        {
                            "spec": "cuda@11.8.0+allow-unsupported-compilers",
                            "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                        }
                    ],
                    "buildable": False,
                },
                "cub": {
                    "externals": [
                        {
                            "spec": "cub@11.8.0",
                            "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                        }
                    ],
                    "buildable": False,
                },
                "cublas": {
                    "externals": [
                        {
                            "spec": "cublas@11.8.0",
                            "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                        }
                    ],
                    "buildable": False,
                },
                "cusolver": {
                    "externals": [
                        {
                            "spec": "cusolver@11.8.0",
                            "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                        }
                    ],
                    "buildable": False,
                },
            }

        if self.spec.satisfies("lapack=cusolver"):
            if self.spec.satisfies("cuda=10.1.243"):
                selections["packages"] |= {
                    "cusolver": {
                        "externals": [
                            {
                                "spec": "cusolver@10.1.243",
                                "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                            }
                        ],
                        "buildable": False,
                    }
                }
            elif self.spec.satisfies("cuda=11.8.0"):
                selections["packages"] |= {
                    "cusolver": {
                        "externals": [
                            {
                                "spec": "cusolver@11.8.0",
                                "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                            }
                        ],
                        "buildable": False,
                    }
                }
        elif self.spec.satisfies("lapack=essl"):
            selections["packages"] |= {
                "essl": {
                    "externals": [
                        {
                            "spec": "essl@6.2 +lapackforessl",
                            "prefix": "/opt/ibmmath/essl/6.2",
                        }
                    ],
                    "buildable": False,
                }
            }

        if self.spec.satisfies("blas=cublas"):
            if self.spec.satisfies("cuda=10.1.243"):
                selections["packages"] |= {
                    "cublas": {
                        "externals": [
                            {
                                "spec": "cublas@10.1.243",
                                "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                            }
                        ],
                        "buildable": False,
                    }
                }
            elif self.spec.satisfies("cuda=11.8.0"):
                selections["packages"] |= {
                    "cublas": {
                        "externals": [
                            {
                                "spec": "cublas@11.8.0",
                                "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                            }
                        ],
                        "buildable": False,
                    }
                }
        elif self.spec.satisfies("blas=essl"):
            selections["packages"] |= {
                "essl": {
                    "externals": [
                        {
                            "spec": "essl@6.2 +lapackforessl",
                            "prefix": "/opt/ibmmath/essl/6.2",
                        }
                    ],
                    "buildable": False,
                }
            }

        mpi_cfgs = {
            (
                "clang-ibm",
                "11-8-0",
            ): [
                {
                    "spec": "spectrum-mpi@2023.06.28-clang-ibm-16.0.6-cuda-11.8.0-gcc-11.2.1",
                    "prefix": "/usr/tce/packages/spectrum-mpi/spectrum-mpi-rolling-release-clang-ibm-16.0.6-cuda-11.8.0-gcc-11.2.1",
                    "extra_attributes": {
                        "extra_link_flags": "-L/usr/tce/packages/spectrum-mpi/spectrum-mpi-rolling-release-clang-ibm-16.0.6-cuda-11.8.0-gcc-11.2.1 -lmpiprofilesupport -lmpi_ibm_usempi -lmpi_ibm_mpifh -lmpi_ibm",
                        "ldflags": "-lmpiprofilesupport -lmpi_ibm_usempi -lmpi_ibm_mpifh -lmpi_ibm",
                    },
                }
            ],
            (
                "xl-gcc",
                "11-8-0",
            ): [
                {
                    "spec": "spectrum-mpi@2023.06.28-cuda-11.8.0-gcc-11.2.1",
                    "prefix": "/usr/tce/packages/spectrum-mpi/spectrum-mpi-rolling-release-xl-2023.06.28-cuda-11.8.0-gcc-11.2.1",
                    "extra_attributes": {
                        "ldflags": "-lmpiprofilesupport -lmpi_ibm_usempi -lmpi_ibm_mpifh -lmpi_ibm"
                    },
                }
            ],
            (
                "xl",
                "10-1-243",
            ): [
                {
                    "spec": "spectrum-mpi@2022.08.19-cuda-10.1.243",
                    "prefix": "/usr/tce/packages/spectrum-mpi/spectrum-mpi-rolling-release-xl-2022.08.19-cuda-10.1.243",
                    "extra_attributes": {
                        "ldflags": "-lmpiprofilesupport -lmpi_ibm_usempi -lmpi_ibm_mpifh -lmpi_ibm"
                    },
                }
            ],
            (
                "clang",
                "11-8-0",
            ): [
                {
                    "spec": "spectrum-mpi@2022.08.19-clang16.0.6-cuda-11.8.0",
                    "prefix": "/usr/tce/packages/spectrum-mpi/spectrum-mpi-rolling-release-clang-16.0.6-cuda-11.8.0-gcc-11.2.1",
                    "extra_attributes": {
                        "ldflags": "-lmpiprofilesupport -lmpi_ibm_usempi -lmpi_ibm_mpifh -lmpi_ibm"
                    },
                }
            ],
            (
                "xl",
                "11-8-0",
            ): [
                {
                    "spec": "spectrum-mpi@2022.08.19-cuda-11.8.0",
                    "prefix": "/usr/tce/packages/spectrum-mpi/spectrum-mpi-rolling-release-xl-2022.08.19-cuda-11.8.0",
                    "extra_attributes": {
                        "ldflags": "-lmpiprofilesupport -lmpi_ibm_usempi -lmpi_ibm_mpifh -lmpi_ibm"
                    },
                }
            ],
        }

        compiler = self.spec.variants["compiler"][0]
        cuda_ver = self.spec.variants["cuda"][0].replace(".", "-")
        cfg = mpi_cfgs[(compiler, cuda_ver)]
        selections["packages"] |= {
            "blas": {"require": [self.spec.variants["blas"][0]]},  # Replace dynamically
            "lapack": {
                "require": [self.spec.variants["lapack"][0]]  # Replace dynamically
            },
            "mpi": {
                "externals": cfg,  # Replace dynamically with the value of `cfg`
                "buildable": False,
            },
        }
        return selections

    def compute_compilers_section(self):
        # values=("clang-ibm", "xl", "xl-gcc", "clang"),
        compiler = self.spec.variants["compiler"][0]
        # values=("11-8-0", "10-1-243"),
        cuda_ver = self.spec.variants["cuda"][0].replace(".", "-")

        cuda_module_map = {
            "11-8-0": ["cuda/11.8.0"],
            "10-1-243": ["cuda/10.1.243"],
        }
        cuda_modules = cuda_module_map[cuda_ver]

        if (compiler, cuda_ver) == ("clang-ibm", "11-8-0"):
            cfg1 = compiler_section_for(
                "llvm",
                [
                    compiler_def(
                        "llvm@16.0.6",
                        "/usr/tce/packages/clang/clang-ibm-16.0.6-cuda-11.8.0-gcc-11.2.1/",
                        {"c": "clang", "cxx": "clang++"},
                        modules=cuda_modules
                        + ["clang/ibm-16.0.6-cuda-11.8.0-gcc-11.2.1"],
                    )
                ],
            )
            cfg2 = compiler_section_for(
                "xl",
                [
                    compiler_def(
                        "xl@2023.06.28",
                        "/usr/tce/packages/xl/xl-2023.06.28-cuda-11.8.0-gcc-11.2.1/",
                        {"c": "xlc", "cxx": "xlC", "fortran": "xlf"},
                    )
                ],
            )
            cfg = merge_dicts(cfg1, cfg2, hybrid_compiler_requirements("llvm", "xl"))
        elif (compiler, cuda_ver) == ("xl-gcc", "11-8-0"):
            cfg = compiler_section_for(
                "xl",
                [
                    compiler_def(
                        "xl@2023.06.28",
                        "/usr/tce/packages/xl/xl-2023.06.28-cuda-11.8.0-gcc-11.2.1/",
                        {"c": "xlc", "cxx": "xlC", "fortran": "xlf"},
                        modules=cuda_modules + ["xl/2023.06.28-cuda-11.8.0-gcc-11.2.1"],
                    )
                ],
            )
        elif (compiler, cuda_ver) == ("xl", "10-1-243"):
            cfg = compiler_section_for(
                "xl",
                [
                    compiler_def(
                        "xl@16.1.1-2022.08.19-cuda10.1.243",
                        "/usr/tce/packages/xl/xl-2022.08.19/",
                        {"c": "xlc", "cxx": "xlC", "fortran": "xlf"},
                        modules=cuda_modules + ["xl/2022.08.19"],
                    )
                ],
            )
        elif (compiler, cuda_ver) == ("xl", "11-8-0"):
            cfg = compiler_section_for(
                "xl",
                [
                    compiler_def(
                        "xl@16.1.1-2022.08.19-cuda11.8.0",
                        "/usr/tce/packages/xl/xl-2022.08.19-cuda-11.8.0/",
                        {"c": "xlc", "cxx": "xlC", "fortran": "xlf"},
                        modules=cuda_modules + ["xl/2022.08.19-cuda-11.8.0"],
                    )
                ],
            )
        elif (compiler, cuda_ver) == ("clang", "11-8-0"):
            cfg1 = compiler_section_for(
                "llvm",
                [
                    compiler_def(
                        "llvm@16.0.6",
                        "/usr/tce/packages/clang/clang-ibm-16.0.6-cuda-11.8.0-gcc-11.2.1/",
                        {"c": "clang", "cxx": "clang++"},
                    )
                ],
            )
            cfg2 = compiler_section_for(
                "gcc",
                [
                    compiler_def(
                        "gcc@11.2.1 languages:=c,c++,fortran",
                        "/usr/tce/packages/gcc/gcc-11.2.1/",
                        {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                    )
                ],
            )
            cfg = merge_dicts(cfg1, cfg2, hybrid_compiler_requirements("llvm", "gcc"))

        return cfg

    def compute_software_section(self):
        """This is somewhat vestigial: for the Tioga config that is committed
        to the repo, multiple instances of mpi/compilers are stored and
        and these variables were used to choose consistent dependencies.
        The configs generated by this class should only ever have one
        instance of MPI etc., so there is no need for that. The experiments
        will fail if these variables are not defined though, so for now
        they are still generated (but with more-generic values).
        """
        compiler_id = self.spec.variants["compiler"][0]
        if compiler_id == "clang-ibm":
            compiler_id = "clang"
        elif compiler_id == "xl-gcc":
            compiler_id = "xl"

        return {
            "software": {
                "packages": {
                    "default-compiler": {"pkg_spec": f"{compiler_id}"},
                    "default-mpi": {"pkg_spec": "spectrum-mpi"},
                    "compiler-xl": {"pkg_spec": "xl"},
                    "mpi-xl": {"pkg_spec": "spectrum-mpi"},
                    "compiler-clang": {"pkg_spec": "clang"},
                    "mpi-clang": {"pkg_spec": "spectrum-mpi"},
                    "mpi-gcc": {"pkg_spec": "spectrum-mpi"},
                    "compiler-clang-ibm": {"pkg_spec": "clang"},
                    "mpi-clang-ibm": {"pkg_spec": "spectrum-mpi"},
                    "blas": {"pkg_spec": f"{self.spec.variants['blas'][0]}"},
                    "blas-cuda": {"pkg_spec": "cublas"},
                    "lapack": {"pkg_spec": f"{self.spec.variants['lapack'][0]}"},
                    "lapack-cuda": {"pkg_spec": "cusolver"},
                }
            }
        }
