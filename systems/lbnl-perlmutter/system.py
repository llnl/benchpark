# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import variant, maintainers
from benchpark.cudasystem import CudaSystem
from benchpark.system import (
    System,
    compiler_section_for,
    compiler_def,
    JobQueue,
    merge_dicts,
)
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from packaging.version import Version
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
            "queues": [JobQueue("regular", 2880, 3072), JobQueue("debug", 30, 8)],
        },
    }

    variant(
        "compiler",
        default="gcc",
        description="Which compiler to use",
    )

    variant(
        "constraint",
        default="cpu",
        values=("cpu", "gpu", "gpu&hbmg40", "gpu&hbmg80"),
        description="Which constraint to use"
    )

    variant(
        "gtl",
        default=False,
        values=(True, False),
        description="Use GTL-enabled MPI",
    )

    variant(
        "queue",
        default="regular",
        values=("none", "regular", "debug"),
        multi=False,
        description="Submit to queue",
    )

    variant(
        "cuda",
        default="12.4",
        values=("12.2", "12.4"),
        description="CUDA version",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [CudaSystem(), OpenMPCPUOnlySystem()]

        self.gcc_version = Version("12.3.0")
        self.mpi_version = Version("8.1.30")
        self.cce_version = Version("16.0.0")
        self.cuda_version = Version(self.spec.variants["cuda"][0])
        self.gtl_flag = self.spec.variants["gtl"][0]

        self.scheduler = "slurm"
        attrs = self.id_to_resources.get("perlmutter")
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_compilers_section(self):
#        nvhpc_cfg = compiler_section_for(
#            "nvhpc",
#            [
#                compiler_def(
#                    "cray-mpich@8.1.30",
#                    "/opt/cray/pe/craype/2.7.32/",
#                    {"c": "cc", "cxx": "CC", "fortran": "ftn"},
#                    modules=["PrgEnv-cray/8.5.0", "craype/2.7.32"],
#                )
#            ],
#        )
#        if self.spec.satisfies("compiler=gcc"):
#            gcc_cfg = compiler_section_for(
#                "gcc",
#                [
#                    compiler_def(
#                        "gcc@12.3.0 languages:=c,c++,fortran",
#                        f"/opt/cray/pe/gcc-native/12/",
#                        {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
#                        modules=["PrgEnv-gnu", "gcc/12.3.0"],
#                        compilers_use_relative_paths=True,
#                            env={
#                                "append_path": {
#                                    "LD_LIBRARY_PATH": "/opt/cray/libfabric/1.22.0/lib64/:/opt/nvidia/hpc_sdk/Linux_x86_64/24.5/cuda/12.4/lib64"
#                                }
#                            },
#                    )
#                ],
#            )
#            cfg = merge_dicts(nvhpc_cfg, gcc_cfg)
#        else:
#            cfg = nvhpc_cfg
#
#        return cfg
        return compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@12.3.0 languages:=c,c++,fortran",
                    f"/opt/cray/pe/gcc-native/12/",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                    modules=["PrgEnv-gnu", "gcc/12.3.0"],
                    compilers_use_relative_paths=True,
                        env={
                            "append_path": {
                                "LD_LIBRARY_PATH": "/opt/cray/libfabric/1.22.0/lib64/:/opt/nvidia/hpc_sdk/Linux_x86_64/24.5/cuda/12.4/lib64"
                            }
                        },
                )
            ],
        )

    def compute_packages_section(self):

        selections = {
            "packages": {
                "all": {"providers": {"mpi": ["cray-mpich"]}},
                "cray-mpich": {
                    "externals": [
                        {
                            "spec": "cray-mpich@8.1.30",
                            "prefix": f"/opt/cray/pe/mpich/8.1.30/ofi/gnu/12.3/",
                        }
                    ],
                    "buildable": False,
                },
                "zlib": {
                    "externals": [{"spec": "zlib@1.2.13", "prefix": "/usr"}],
                    "buildable": False,
                },
                "gmake": {
                    "externals": [{"spec": "gmake@4.2.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "cmake": {
                    "externals": [{"spec": "cmake@3.30.2", "prefix": "/global/common/software/nersc9/cmake/3.30.2"}],
                    "buildable": False,
                },
                "mpi": {"buildable": False},
            }
        }

        if self.spec.satisfies("compiler=gcc"):
            selections["packages"] |= {
                "cray-libsci": {
                    "externals": [
                        {
                            "spec": "cray-libsci@24.07.0", 
                            "prefix": "/opt/cray/pe/libsci/24.07.0/GNU/12.3/x86_64/",
                        }
                    ],
                    "buildable": False,
                }
            }
        else:
            selections["packages"] |= {
                "cray-libsci": {
                    "externals": [
                        {
                            "spec": "cray-libsci@24.07.0",
                            "prefix": "/opt/cray/pe/libsci/24.07.0/CRAY/17.0/x86_64/",
                        }
                    ],
                    "buildable": False,
                }
            }

        selections["packages"] |= self.cuda_config(self.spec.variants["cuda"][0])[
            "packages"
        ]

        return selections

    def system_specific_variables(self):
        opts = super().system_specific_variables()
        if self.spec.satisfies("constraint=cpu"):
            opts.update(
                {
                    "extra_batch_opts":f"--constraint={self.spec.variants['constraint'][0]}",
                }
            )
        elif self.spec.satisfies("constraint=gpu"):
            opts.update(
                {
                    "extra_batch_opts":f"--constraint={self.spec.variants['constraint'][0]}",
                }
            )
        elif self.spec.satisfies("constraint=gpu&hbmg40"):
            opts.update(
                {
                    "extra_batch_opts":f"--constraint={self.spec.variants['constraint'][0]}",
                }
            )
        elif self.spec.satisfies("constraint=gpu&hbmg80"):
            opts.update(
                {
                    "extra_batch_opts":f"--constraint={self.spec.variants['constraint'][0]}",
                }
            )
        
        return opts

    def cuda_config(self, cuda_version):
        return {
            "packages": {
                "blas": {"require": "intel-oneapi-mkl"},
                "lapack": {"require": "intel-oneapi-mkl"},
                "curand": {
                    "externals": [
                        {
                            "spec": f"curand@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/24.5/math_libs/12.4/lib64",
                        }
                    ],
                    "buildable": False,
                },
                "cuda": {
                    "externals": [
                        {
                            "spec": f"cuda@{cuda_version}+allow-unsupported-compilers",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/24.5/cuda/{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cub": {
                    "externals": [
                        {
                            "spec": f"cub@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/24.5/cuda/{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
#                "cusparse": {
#                    "externals": [
#                        {
#                            "spec": f"cusparse@{cuda_version}",
#                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/24.5/cuda/{cuda_version}",
#                        }
#                    ],
#                    "buildable": False,
#                },
                "cublas": {
                    "externals": [
                        {
                            "spec": f"cublas@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/24.5/math_libs/12.4/lib64",
                        }
                    ],
                    "buildable": False,
                },
                "cusolver": {
                    "externals": [
                        {
                            "spec": f"cusolver@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/24.5/math_libs/12.4/lib64",
                        }
                    ],
                    "buildable": False,
                },
                "cufft": {
                    "externals": [
                        {
                            "spec": f"cufft@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/24.5/math_libs/12.4/lib64",
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
                    "default-compiler": {"pkg_spec": "gcc@12.3.0"},
                    "default-mpi": {"pkg_spec": "cray-mpich@8.1.28"},
                    "compiler-gcc": {"pkg_spec": "gcc@12.3.0"},
                }
            }
        }
