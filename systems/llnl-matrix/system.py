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
    merge_dicts,
)


class LlnlMatrix(System):

    maintainers("pearce8", "michaelmckinsey1")

    id_to_resources = {
        "matrix": {
            "cuda_arch": 90,
            "sys_cores_per_node": 112,
            "sys_gpus_per_node": 4,
            "system_site": "llnl",
            "hardware_key": str(hardware_descriptions)
            + "/DELL-sapphirerapids-H100-Infiniband/hardware_description.yaml",
            "queues": [JobQueue("pdebug", 60, 1), JobQueue("pbatch", 1440, 28)],
        },
    }

    variant(
        "cuda",
        default="12.6.0",
        values=("12.6.0", "12.2.2", "11.8.0"),
        description="CUDA version",
    )

    variant(
        "compiler",
        default="gcc",
        values=("oneapi", "gcc", "intel"),
        description="Which compiler to use",
    )

    variant(
        "mpi",
        default="mvapich2",
        values=("mvapich2", "openmpi"),
        description="Which MPI implementation to use",
    )

    variant(
        "bank",
        default="none",
        values=("none", "guests", "asccasc", "lc", "fractale", "wbronze"),
        multi=False,
        description="Submit a job to a specific named bank",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [CudaSystem(), OpenMPCPUOnlySystem()]
        self.cuda_version = Version(self.spec.variants["cuda"][0])
        self.gtl_flag = False

        self.scheduler = "slurm"
        attrs = self.id_to_resources.get("matrix")
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):
        selections = {
            "packages": {
                "elfutils": {
                    "externals": [{"spec": "elfutils@0.190", "prefix": "/usr"}],
                    "buildable": False,
                },
                "papi": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "papi@6.0.0.1",
                            "prefix": "/usr/tce/packages/papi/papi-6.0.0.1",
                        }
                    ],
                },
                "unwind": {
                    "externals": [{"spec": "unwind@8.0.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "fftw": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "fftw@3.3.10",
                            "prefix": "/usr/tce/packages/fftw/fftw-3.3.10",
                        }
                    ],
                },
                "intel-oneapi-mkl": {
                    "externals": [
                        {
                            "spec": "intel-oneapi-mkl@2023.2.0",
                            "prefix": "/opt/intel/oneapi",
                        }
                    ],
                    "buildable": False,
                },
                "blas": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "intel-oneapi-mkl@2023.2.0",
                            "prefix": "/opt/intel/oneapi",
                        }
                    ],
                },
                "lapack": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "intel-oneapi-mkl@2023.2.0",
                            "prefix": "/opt/intel/oneapi",
                        }
                    ],
                },
                "diffutils": {
                    "externals": [{"spec": "diffutils@3.6", "prefix": "/usr"}],
                    "buildable": False,
                },
                "cmake": {
                    "externals": [
                        {"spec": "cmake@3.26.5", "prefix": "/usr"},
                        {"spec": "cmake@3.23.1", "prefix": "/usr/tce"},
                    ],
                    "buildable": False,
                },
                "tar": {
                    "externals": [{"spec": "tar@1.30", "prefix": "/usr"}],
                    "buildable": False,
                },
                "autoconf": {
                    "externals": [{"spec": "autoconf@2.69", "prefix": "/usr"}],
                    "buildable": False,
                },
                "python": {
                    "externals": [
                        {
                            "spec": "python@3.9.12+bz2+crypt+ctypes+dbm+lzma+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib",
                            "prefix": "/usr/tce",
                        },
                    ],
                    "buildable": False,
                },
                "hwloc": {
                    "externals": [{"spec": "hwloc@2.11.2", "prefix": "/usr"}],
                    "buildable": False,
                },
                "gmake": {
                    "externals": [{"spec": "gmake@4.2.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "curl": {
                    "externals": [{"spec": "curl@7.61.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "mpi": {"buildable": False},
            }
        }

        mpi_type = self.spec.variants["mpi"][0]
        mpi_dict = {
            "mpi": {
                "buildable": False,
            },
        }
        if self.spec.satisfies("compiler=gcc"):
            if mpi_type == "mvapich2":
                mpi_dict["mvapich2"] = {
                    "externals": [
                        {
                            "spec": "mvapich2@2.3.7",
                            "prefix": "/usr/tce/packages/mvapich2/mvapich2-2.3.7-gcc-12.1.1",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/mvapich2/mvapich2-2.3.7-gcc-12.1.1/lib -lmpi"
                            },
                        }
                    ],
                }
            elif mpi_type == "openmpi":
                mpi_dict["openmpi"] = {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.2",
                            "prefix": "/usr/tce/packages/openmpi/openmpi-4.1.2-gcc-12.1.1",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/openmpi/openmpi-4.1.2-gcc-12.1.1/lib -lmpi"
                            },
                        }
                    ],
                }
        elif self.spec.satisfies("compiler=intel"):
            if mpi_type == "mvapich2":
                mpi_dict["mvapich2"] = {
                    "externals": [
                        {
                            "spec": "mvapich2@2.3.7",
                            "prefix": "/usr/tce/packages/mvapich2/mvapich2-2.3.7-intel-classic-2021.6.0",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/mvapich2/mvapich2-2.3.7-intel-classic-2021.6.0/lib -lmpi"
                            },
                        }
                    ],
                }
            elif mpi_type == "openmpi":
                mpi_dict["openmpi"] = {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.2",
                            "prefix": "/usr/tce/packages/openmpi/openmpi-4.1.2-intel-classic-2021.6.0",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/openmpi/openmpi-4.1.2-intel-classic-2021.6.0/lib -lmpi"
                            },
                        }
                    ],
                }
        elif self.spec.satisfies("compiler=oneapi"):
            if mpi_type == "mvapich2":
                mpi_dict["mvapich2"] = {
                    "externals": [
                        {
                            "spec": "mvapich2@2.3.7",
                            "prefix": "/usr/tce/packages/mvapich2/mvapich2-2.3.7-intel-2023.2.1",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/mvapich2/mvapich2-2.3.7-intel-2023.2.1/lib -lmpi"
                            },
                        }
                    ],
                }
            elif mpi_type == "openmpi":
                mpi_dict["openmpi"] = {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.2",
                            "prefix": "/usr/tce/packages/openmpi/openmpi-4.1.2-intel-2023.2.1",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/openmpi/openmpi-4.1.2-intel-2023.2.1/lib -lmpi"
                            },
                        }
                    ],
                }

        selections["packages"] |= self.cuda_config(self.spec.variants["cuda"][0])[
            "packages"
        ]
        selections |= {"packages": selections["packages"] | mpi_dict}

        return selections

    def compute_compilers_section(self):
        gcc_cfg = compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@12.1.1 languages:=c,c++,fortran",
                    "/usr/tce/packages/gcc/gcc-12.1.1/",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                )
            ],
        )
        if self.spec.satisfies("compiler=gcc"):
            cfg = gcc_cfg
        elif self.spec.satisfies("compiler=intel"):
            cfg = compiler_section_for(
                "intel-oneapi-compilers-classic",
                [
                    compiler_def(
                        "intel-oneapi-compilers-classic@2021.6.0 ~envmods",
                        "/usr/tce/packages/intel-classic/intel-classic-2021.6.0/",
                        {"c": "icc", "cxx": "icpc", "fortran": "ifort"},
                    )
                ],
            )
        elif self.spec.satisfies("compiler=oneapi"):
            oneapi_cfg = compiler_section_for(
                "intel-oneapi-compilers",
                [
                    compiler_def(
                        "intel-oneapi-compilers@2023.2.1 ~envmods",
                        "/usr/tce/packages/intel/intel-2023.2.1/compiler/2023.2.1/linux/",
                        {"c": "icx", "cxx": "icpx", "fortran": "ifx"},
                        modules=[
                            f"cuda/{self.cuda_version}",
                        ],
                    )
                ],
            )
            prefs = {"one_of": ["%oneapi", "%gcc"], "when": "%c"}
            weighting_cfg = {"packages": {"all": {"require": [prefs]}}}
            cfg = merge_dicts(gcc_cfg, oneapi_cfg, weighting_cfg)

        return cfg

    def cuda_config(self, cuda_version):
        return {
            "packages": {
                "blas": {"require": "intel-oneapi-mkl"},
                "lapack": {"require": "intel-oneapi-mkl"},
                "curand": {
                    "externals": [
                        {
                            "spec": f"curand@{cuda_version}",
                            "prefix": f"/usr/tce/packages/cuda/cuda-{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cuda": {
                    "externals": [
                        {
                            "spec": f"cuda@{cuda_version}+allow-unsupported-compilers",
                            "prefix": f"/usr/tce/packages/cuda/cuda-{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cub": {
                    "externals": [
                        {
                            "spec": f"cub@{cuda_version}",
                            "prefix": f"/usr/tce/packages/cuda/cuda-{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cusparse": {
                    "externals": [
                        {
                            "spec": f"cusparse@{cuda_version}",
                            "prefix": f"/usr/tce/packages/cuda/cuda-{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cublas": {
                    "externals": [
                        {
                            "spec": f"cublas@{cuda_version}",
                            "prefix": f"/usr/tce/packages/cuda/cuda-{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cusolver": {
                    "externals": [
                        {
                            "spec": f"cusolver@{cuda_version}",
                            "prefix": f"/usr/tce/packages/cuda/cuda-{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cufft": {
                    "externals": [
                        {
                            "spec": f"cufft@{cuda_version}",
                            "prefix": f"/usr/tce/packages/cuda/cuda-{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
            }
        }

    def compute_software_section(self):
        default_compiler = "gcc"
        if self.spec.satisfies("compiler=intel"):
            default_compiler = "intel-oneapi-compilers-classic"
        elif self.spec.satisfies("compiler=oneapi"):
            default_compiler = "intel-oneapi-compilers"

        return {
            "software": {
                "packages": {
                    "default-compiler": {"pkg_spec": default_compiler},
                    "compiler-gcc": {"pkg_spec": "gcc"},
                    "compiler-intel": {"pkg_spec": "intel"},
                    "blas": {"pkg_spec": "intel-oneapi-mkl"},
                    "lapack": {"pkg_spec": "intel-oneapi-mkl"},
                }
            }
        }
