# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from packaging.version import Version

from benchpark.cudasystem import CudaSystem
from benchpark.directives import maintainers, variant
from benchpark.paths import hardware_descriptions
from benchpark.system import System, compiler_def, compiler_section_for, merge_dicts


class JscJuwels(System):

    maintainers("pearce8")

    id_to_resources = {
        "juwels": {
            "sys_cores_per_node": 48,
            "timeout": 120,
            "sys_gpus_per_node": 4,
            "cuda_arch": "80",
            "system_site": "jsc",
            "hardware_key": str(hardware_descriptions)
            + "/Atos-rome-A100-Infiniband/hardware_description.yaml",
        }
    }

    variant(
        "cuda",
        default="12.2.0",
        values=("11.8.0", "12.2.0"),
        description="CUDA version",
    )
    variant(
        "compiler",
        default="gcc",
        description="Which compiler to use",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [CudaSystem()]
        self.cuda_version = Version(self.spec.variants["cuda"][0])
        self.gtl_flag = None

        if self.spec.satisfies("compiler=gcc"):
            self.gcc_version = Version("12.3.0")
            self.nvhpc_version = Version("23.7")

        self.scheduler = "slurm"
        attrs = self.id_to_resources.get("juwels")
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_compilers_section(self):
        nvhpc_cfg = compiler_section_for(
            "nvhpc",
            [
                compiler_def(
                    "nvhpc@23.7",
                    "/p/software/juwelsbooster/stages/2024/software/NVHPC/23.7-CUDA-12/Linux_aarch64/23.7/compilers/",
                    {"c": "nvc", "cxx": "nvc++", "fortran": "nvfortran"},
                    modules=["Stages/2024", "NVHPC/23.7"],
                )
            ],
        )

        if self.spec.satisfies("compiler=gcc"):
            gcc_cfg = compiler_section_for(
                "gcc",
                [
                    compiler_def(
                        "gcc@12.3.0 languages:=c,c++,fortran",
                        "/p/software/juwelsbooster/stages/2024/software/GCCcore/12.3.0/",
                        {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                        modules=["Stages/2024", "GCC/12.3.0"],
                    )
                ],
            )
            cfg = merge_dicts(nvhpc_cfg, gcc_cfg)
        else:
            cfg = nvhpc_cfg

        return cfg

    def compute_packages_section(self):

        selections = {
            "packages": {
                "tar": {
                    "externals": [{"spec": "tar@1.30", "prefix": "/usr"}],
                    "buildable": False,
                },
                "cmake": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "cmake@3.26.3",
                            "prefix": "/p/software/juwelsbooster/stages/2024/software/CMake/3.26.3-GCCcore-12.3.0",
                            "modules": ["Stages/2024", "CMake"],
                        }
                    ],
                },
                "gmake": {
                    "externals": [{"spec": "gmake@4.2.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "automake": {
                    "externals": [
                        {
                            "spec": "automake@1.16.5",
                            "prefix": "/p/software/juwelsbooster/stages/2024/software/Automake/1.16.5-GCCcore-12.3.0",
                        }
                    ]
                },
                "autoconf": {
                    "externals": [
                        {
                            "spec": "autoconf@2.71",
                            "prefix": "/p/software/juwelsbooster/stages/2024/software/Autoconf/2.71-GCCcore-12.3.0",
                        }
                    ]
                },
                "openmpi": {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.5",
                            "prefix": "/p/software/juwelsbooster/stages/2024/software/OpenMPI/4.1.5-NVHPC-23.7-CUDA-12",
                            "modules": [
                                "Stages/2024",
                                "NVHPC/23.7-CUDA-12",
                                "OpenMPI/4.1.5",
                            ],
                        }
                    ],
                    "buildable": False,
                },
                "blas": {"buildable": False},
                "lapack": {"buildable": False},
                "openblas": {
                    "externals": [
                        {
                            "spec": "openblas@0.3.23%gcc@12.3.0",
                            "prefix": "/p/software/juwelsbooster/stages/2024/software/OpenBLAS/0.3.23-GCC-12.3.0",
                            "modules": ["Stages/2024", "OpenBLAS"],
                        }
                    ]
                },
                "all": {"providers": {"mpi": ["openmpi"], "zlib-api": ["zlib"]}},
                "zlib": {
                    "externals": [
                        {
                            "spec": "zlib@1.2.13",
                            "prefix": "/p/software/juwelsbooster/stages/2024/software/zlib/1.2.13-GCCcore-12.3.0",
                        }
                    ]
                },
            }
        }

        selections["packages"] |= self.cuda_config()["packages"]

        return selections

    def cuda_config(self):
        return {
            "packages": {
                "cuda": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "cuda@{self.cuda_version}",
                            "prefix": "/p/software/juwelsbooster/stages/2024/software/CUDA/{self.cuda_version.major}",
                            "modules": [
                                "Stages/2024",
                                "CUDA/{self.cuda_version.major}",
                                "NVHPC/23.7-CUDA-{self.cuda_version.major}",
                            ],
                        }
                    ],
                },
                "curand": {
                    "externals": [
                        {
                            "spec": "curand@{self.cuda_version}",
                            "prefix": "/p/software/juwelsbooster/stages/2024/software/CUDA/{self.cuda_version.major}",
                        }
                    ],
                    "buildable": False,
                },
                "cusparse": {
                    "externals": [
                        {
                            "spec": "cusparse@{self.cuda_version}",
                            "prefix": "/p/software/juwelsbooster/stages/2024/software/CUDA/{self.cuda_version.major}",
                        }
                    ],
                    "buildable": False,
                },
                "cublas": {
                    "externals": [
                        {
                            "spec": "cublas@{self.cuda_version}",
                            "prefix": "/p/software/juwelsbooster/stages/2024/software/CUDA/{self.cuda_version.major}",
                        }
                    ],
                    "buildable": False,
                },
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
                    "default-compiler": {"pkg_spec": self.spec.variants["compiler"][0]},
                    "default-mpi": {"pkg_spec": "openmpi@4.1.5"},
                    "compiler-gcc": {"pkg_spec": "gcc"},
                    "cublas-cuda": {"pkg_spec": f"cublas@{self.cuda_version}"},
                    "blas": {"pkg_spec": "openblas@0.3.23"},
                    "lapack": {"pkg_spec": "openblas@0.3.23"},
                }
            }
        }
