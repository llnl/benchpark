# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from packaging.version import Version

from benchpark.cudasystem import CudaSystem
from benchpark.directives import maintainers, variant
from benchpark.paths import hardware_descriptions
from benchpark.system import System, compiler_def, compiler_section_for, merge_dicts


class LanlVenado(System):

    maintainers("rfhaque", "gshipman")

    id_to_resources = {
        "grace-hopper": {
            "cuda_arch": 90,
            "sys_cores_per_node": 144,
            "sys_gpus_per_node": 4,
            "system_site": "lanl",
            "extra_batch_opts": "-A llnl_ai_g -pgpu",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-neoverse-H100-Slingshot/hardware_description.yaml",
        },
        "grace-grace": {
            "sys_cores_per_node": 144,
            "system_site": "lanl",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-neoverse-H100-Slingshot/hardware_description.yaml",
        },
    }

    variant(
        "cluster",
        default="grace-hopper",
        values=("grace-hopper", "grace-grace"),
        description="Which cluster to run on",
    )
    variant(
        "cuda",
        default="12.5",
        values=("11.8", "12.5"),
        description="CUDA version",
    )
    variant(
        "compiler",
        default="cce",
        values=("gcc", "cce"),
        description="Which compiler to use",
    )
    variant(
        "gtl",
        default=False,
        values=(True, False),
        description="Use GTL-enabled MPI",
    )
    variant(
        "lapack",
        default="cray-libsci",
        values=("cray-libsci",),
        description="Which lapack to use",
    )
    variant(
        "blas",
        default="cray-libsci",
        values=("cray-libsci",),
        description="Which blas to use",
    )

    def __init__(self, spec):
        super().__init__(spec)
        if self.spec.variants["cluster"][0] == "grace-hopper":
            self.programming_models = [CudaSystem()]
            self.cuda_version = Version(self.spec.variants["cuda"][0])
            self.gtl_flag = self.spec.variants["gtl"][0]

        self.scheduler = "slurm"
        attrs = self.id_to_resources.get(self.spec.variants["cluster"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):
        selections = {
            "packages": {
                "tar": {
                    "externals": [{"spec": "tar@1.34", "prefix": "/usr"}],
                    "buildable": False,
                },
                "cmake": {
                    "externals": [
                        {
                            "spec": "cmake@3.29.6",
                            "prefix": "/usr/projects/hpcsoft/tce/24-07/cos3-aarch64-cc90/packages/cmake/cmake-3.29.6",
                        }
                    ],
                    "buildable": False,
                },
                "gmake": {
                    "externals": [{"spec": "gmake@4.2.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "automake": {
                    "externals": [{"spec": "automake@1.15.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "autoconf": {
                    "externals": [{"spec": "autoconf@2.69", "prefix": "/usr"}],
                    "buildable": False,
                },
                "fftw": {
                    "externals": [
                        {
                            "spec": "fftw@3.3.10.8",
                            "prefix": "/opt/cray/pe/fftw/3.3.10.8/arm_grace",
                        }
                    ],
                    "buildable": False,
                },
                "python": {
                    "externals": [
                        {
                            "spec": "python@3.10.9",
                            "prefix": "/usr/projects/hpcsoft/common/aarch64/anaconda/2023.03-python-3.10",
                        }
                    ],
                    "buildable": False,
                },
                "mpi": {"buildable": False},
            }
        }

        selections["packages"] |= self.cuda_config(self.spec.variants["cuda"][0])[
            "packages"
        ]

        selections["packages"] |= self.mpi_config()["packages"]

        if self.spec.satisfies("compiler=cce"):
            selections["packages"] |= {
                "cray-libsci": {
                    "externals": [
                        {
                            "spec": "cray-libsci@24.07.0%cce",
                            "prefix": "/opt/cray/pe/libsci/24.07.0/cray/17.0/aarch64",
                        }
                    ]
                }
            }
        elif self.spec.satisfies("compiler=gcc"):
            selections["packages"] |= {
                "cray-libsci": {
                    "externals": [
                        {
                            "spec": "cray-libsci@24.07.0%gcc",
                            "prefix": "/opt/cray/pe/libsci/24.07.0/gnu/12.3/aarch64",
                        }
                    ]
                }
            }

        return selections

    def compute_compilers_section(self):
        gcc_cfg = compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@12.3.0 languages:=c,c++,fortran",
                    "/usr/projects/hpcsoft/tce/24-07/cos3-aarch64-cc90/compilers/gcc/12.3.0/",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                )
            ],
        )

        # TODO: Construct/extract/customize compiler information from the working set
        if self.spec.satisfies("compiler=cce"):
            cce_cfg = compiler_section_for(
                "cce",
                [
                    compiler_def(
                        "cce@18.0.0",
                        "/opt/cray/pe/cce/18.0.0/",
                        {"c": "cracc", "cxx": "crayCC", "fortran": "crayftn"},
                        env={
                            "prepend_path": {
                                "LD_LIBRARY_PATH": "/opt/cray/pe/cce/18.0.0/cce/aarch64/lib:/opt/cray/libfabric/1.20.1/lib64:/usr/projects/hpcsoft/tce/24-07/cos3-aarch64-cc90/compilers/gcc/12.3.0/lib:/usr/projects/hpcsoft/tce/24-07/cos3-aarch64-cc90/compilers/gcc/12.3.0/lib64:/opt/cray/pe/gcc-libs"
                            }
                        },
                        extra_rpaths=[
                            "/opt/cray/pe/gcc-libs",
                            "/opt/cray/pe/cce/18.0.0/cce/aarch64/lib",
                            "/opt/cray/libfabric/1.20.1/lib64",
                            "/usr/projects/hpcsoft/tce/24-07/cos3-aarch64-cc90/compilers/gcc/12.3.0/lib",
                            "/usr/projects/hpcsoft/tce/24-07/cos3-aarch64-cc90/compilers/gcc/12.3.0/lib64",
                        ],
                    )
                ],
            )
            cfg = merge_dicts(gcc_cfg, cce_cfg)
        else:
            cfg = gcc_cfg

        return cfg

    def mpi_config(self):
        mpi_version = "8.1.30"
        gtl = (
            "+gtl"
            if self.spec.satisfies("compiler=cce") and self.spec.satisfies("+gtl")
            else "~gtl"
        )

        # TODO: Construct/extract this information from the working set
        if self.spec.satisfies("compiler=cce"):
            compiler = "cce@18.0.0"
            mpi_compiler_suffix = "crayclang/17.0"
        elif self.spec.satisfies("compiler=gcc"):
            compiler = "gcc@12.3.0"
            mpi_compiler_suffix = "gnu/12.3"

        return {
            "packages": {
                "cray-mpich": {
                    "externals": [
                        {
                            "spec": f"cray-mpich@{mpi_version}%{compiler} {gtl} +wrappers",
                            "prefix": f"/opt/cray/pe/mpich/{mpi_version}/ofi/{mpi_compiler_suffix}",
                            "extra_attributes": {
                                "gtl_lib_path": f"/opt/cray/pe/mpich/{mpi_version}/gtl/lib",
                                "gtl_libs": "libmpi_gtl_cuda",
                                "ldflags": f"-L/opt/cray/pe/mpich/{mpi_version}/ofi/{mpi_compiler_suffix}/lib -lmpi -L/opt/cray/pe/mpich/{mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{mpi_version}/gtl/lib -lmpi_gtl_cuda",
                            },
                        }
                    ]
                }
            }
        }

    def cuda_config(self, cuda_version):
        return {
            "packages": {
                "blas": {"require": [f"{self.spec.variants['blas'][0]}"]},
                "lapack": {"require": [f"{self.spec.variants['lapack'][0]}"]},
                "curand": {
                    "externals": [
                        {
                            "spec": f"curand@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/24.7/cuda/{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cusparse": {
                    "externals": [
                        {
                            "spec": f"cusparse@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/24.7/cuda/{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cuda": {
                    "externals": [
                        {
                            "spec": f"cuda@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/24.7/cuda/{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cub": {
                    "externals": [
                        {
                            "spec": f"cub@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/24.7/cuda/{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cublas": {
                    "externals": [
                        {
                            "spec": f"cublas@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/24.7/math_libs/{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cusolver": {
                    "externals": [
                        {
                            "spec": f"cusolver@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/24.7/math_libs/{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cufft": {
                    "externals": [
                        {
                            "spec": f"cufft@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/24.7/math_libs/{cuda_version}",
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
                    "default-compiler": {
                        "pkg_spec": f"{self.spec.variants['compiler'][0]}"
                    },
                    "default-mpi": {"pkg_spec": "cray-mpich"},
                    "default-lapack": {
                        "pkg_spec": f"{self.spec.variants['lapack'][0]}"
                    },
                    "default-blas": {"pkg_spec": f"{self.spec.variants['blas'][0]}"},
                }
            }
        }
