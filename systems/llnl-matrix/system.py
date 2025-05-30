# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.cudasystem import CudaSystem
from benchpark.paths import hardware_descriptions
from benchpark.system import System
from packaging.version import Version


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
        },
    }

    variant(
        "cuda",
        default="11.8.0",
        values=("12.2.2", "11.8.0", "10.2.89"),
        description="CUDA version",
    )
    variant(
        "compiler",
        default="gcc",
        values=("gcc", "intel"),
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

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [CudaSystem()]
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
                "blas": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "intel-oneapi-mkl@2022.1.0",
                            "prefix": "/usr/tce/backend/installations/linux-rhel8-x86_64/intel-19.0.4/intel-oneapi-mkl-2022.1.0-sksz67twjxftvwchnagedk36gf7plkrp",
                        }
                    ],
                },
                "lapack": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "intel-oneapi-mkl@2022.1.0",
                            "prefix": "/usr/tce/backend/installations/linux-rhel8-x86_64/intel-19.0.4/intel-oneapi-mkl-2022.1.0-sksz67twjxftvwchnagedk36gf7plkrp",
                        }
                    ],
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
            }
        }

        if self.spec.satisfies("compiler=gcc"):
            selections |= {
                "packages": selections["packages"]
                | {
                    "mpi": {
                        "buildable": False,
                        "externals": [
                            {
                                "spec": "mvapich2@2.3.7-gcc1211",
                                "prefix": "/usr/tce/packages/mvapich2/mvapich2-2.3.7-gcc-12.1.1",
                                "extra_attributes": {
                                    "ldflags": "-L/usr/tce/packages/mvapich2/mvapich2-2.3.7-gcc-12.1.1/lib -lmpi"
                                },
                            }
                        ],
                    }
                }
            }
        elif self.spec.satisfies("compiler=intel"):
            selections |= {
                "packages": selections["packages"]
                | {
                    "mpi": {
                        "buildable": False,
                        "externals": [
                            {
                                "spec": "mvapich2@2.3.7-intel202160classic",
                                "prefix": "/usr/tce/packages/mvapich2/mvapich2-2.3.7-intel-classic-2021.6.0",
                                "extra_attributes": {
                                    "ldflags": "-L/usr/tce/packages/mvapich2/mvapich2-2.3.7-intel-classic-2021.6.0/lib -lmpi"
                                },
                            }
                        ],
                    }
                }
            }

        return selections


    def compute_compilers_section(self):
        selections = {}
        if self.spec.satisfies("compiler=gcc"):
            selections = {
                "compilers": [
                    {
                        "compiler": {
                            "spec": "gcc@12.1.1",
                            "paths": {
                                "cc": "/usr/tce/packages/gcc/gcc-12.1.1/bin/gcc",
                                "cxx": "/usr/tce/packages/gcc/gcc-12.1.1/bin/g++",
                                "f77": "/usr/tce/packages/gcc/gcc-12.1.1/bin/gfortran",
                                "fc": "/usr/tce/packages/gcc/gcc-12.1.1/bin/gfortran",
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
        elif self.spec.satisfies("compiler=intel"):
            selections = {
                "compilers": [
                    {
                        "compiler": {
                            "spec": "intel@2021.6.0-classic",
                            "paths": {
                                "cc": "/usr/tce/packages/intel-classic/intel-classic-2021.6.0/bin/icc",
                                "cxx": "/usr/tce/packages/intel-classic/intel-classic-2021.6.0/bin/icpc",
                                "f77": "/usr/tce/packages/intel-classic/intel-classic-2021.6.0/bin/ifort",
                                "fc": "/usr/tce/packages/intel-classic/intel-classic-2021.6.0/bin/ifort",
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
      
    def compute_software_section(self):
        return {
            "software": {
                "packages": {
                    "default-compiler": {"pkg_spec": self.spec.variants["compiler"][0]},
                    "default-mpi": {"pkg_spec": "mvapich2"},
                    "compiler-gcc": {"pkg_spec": "gcc"},
                    "compiler-intel": {"pkg_spec": "intel"},
                    "blas": {"pkg_spec": "intel-oneapi-mkl"},
                    "lapack": {"pkg_spec": "intel-oneapi-mkl"},
                    "mpi-gcc": {"pkg_spec": "mvapich2"},
                    "mpi-intel": {"pkg_spec": "mvapich2"},
                }
            }
        }
