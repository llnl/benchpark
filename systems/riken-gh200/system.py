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
    System,
    compiler_def,
    compiler_section_for,
    merge_dicts,
)


class RikenGh200(System):

    maintainers("jdomke", "SBA0486")

    id_to_resources = {
        "gh200": {
            "sys_cores_per_node": 72,
            "sys_gpus_per_node": 1,
            "sys_mem_per_node_GB": 512,
            "system_site": "rccs",
            "queue": "qc-gh200",
            "hardware_key": str(hardware_descriptions)
            + "/NVIDIA-neoverse-GH200-Infiniband/hardware_description.yaml",
        },
    }

    variant(
        "compiler",
        default="gcc",
        values=("gcc", "nvhpc", "cuda"),
        description="Which compiler to use",
    )
    variant(
        "cuda",
        default="12.9",
        values=("12.3", "12.4", "12.5", "12.6", "12.8", "12.9", "13.0", "13.1", "13.2"),
        description="CUDA version",
    )
    variant(
        "nvhpc",
        default="25.7",
        values=("26.3", "25.9", "25.7", "24.9", "24.3"),
        description="NVHPC version",
    )
    variant(
        "gtl",
        default=False,
        values=(True, False),
        description="Use GTL-enabled MPI",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [CudaSystem(), OpenMPCPUOnlySystem()]
        self.cuda_version = Version(self.spec.variants["cuda"][0])
        self.gtl_flag = self.spec.variants["gtl"][0]
        self.nvhpc_version = Version(self.spec.variants["nvhpc"][0])
        if str(self.nvhpc_version) == "26.3":
            self.cuda_version = "13.1"
        if str(self.nvhpc_version) == "25.9":
            self.cuda_version = "13.0"
        if str(self.nvhpc_version) == "25.7":
            self.cuda_version = "12.9"
        if str(self.nvhpc_version) == "24.9":
            self.cuda_version = "12.6"
        if str(self.nvhpc_version) == "24.3":
            self.cuda_version = "12.3"
        self.scheduler = "slurm"

        attrs = self.id_to_resources.get("gh200")
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):
        selections = {
            "packages": {
                "all": {
                    "providers": {
                        "mpi": ["fujitsu-mpi", "openmpi", "mpich"],
                        "blas": ["fujitsu-ssl2", "openblas"],
                        "lapack": ["fujitsu-ssl2", "openblas"],
                        "scalapack": ["fujitsu-ssl2", "netlib-scalapack"],
                        "fftw-api": ["fujitsu-fftw", "fftw", "rist-fftw"],
                    },
                    "permissions": {"write": "group"},
                },
                "autoconf": {
                    "externals": [
                        {
                            "spec": "autoconf@2.69",
                            "prefix": "/usr",
                        }
                    ]
                },
                "automake": {
                    "externals": [
                        {
                            "spec": "automake@1.16.2",
                            "prefix": "/usr",
                        }
                    ]
                },
                "binutils": {
                    "externals": [
                        {
                            "spec": "binutils@2.35.2~gold~headers",
                            "prefix": "/usr",
                        }
                    ]
                },
                "bzip2": {
                    "externals": [
                        {
                            "spec": "bzip2@1.0.6 arch=linux-rhel8-a64fx",
                            "prefix": "/usr",
                        }
                    ]
                },
                "bison": {
                    "externals": [
                        {
                            "spec": "bison@3.7.4",
                            "prefix": "/usr",
                        }
                    ]
                },
                "cmake": {
                    "externals": [
                        {
                            "spec": "cmake@3.26.5",
                            "prefix": "/usr",
                        }
                    ]
                },
                "coreutils": {
                    "externals": [
                        {
                            "spec": "coreutils@8.32",
                            "prefix": "/usr",
                        }
                    ]
                },
                "curl": {
                    "externals": [
                        {
                            "spec": "curl@7.76.1+gssapi+ldap+nghttp2",
                            "prefix": "/usr",
                        }
                    ]
                },
                "diffutils": {
                    "externals": [
                        {
                            "spec": "diffutils@3.7",
                            "prefix": "/usr",
                        }
                    ]
                },
                "findutils": {
                    "externals": [
                        {
                            "spec": "findutils@4.8.0",
                            "prefix": "/usr",
                        }
                    ]
                },
                "flex": {
                    "externals": [
                        {
                            "spec": "flex@2.6.4+lex",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gawk": {
                    "externals": [
                        {
                            "spec": "gawk@5.1.0",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gettext": {
                    "externals": [
                        {
                            "spec": "gettext@0.21",
                            "prefix": "/usr",
                        }
                    ]
                },
                "git": {
                    "externals": [
                        {
                            "spec": "git@2.47.3~tcltk",
                            "prefix": "/usr",
                        }
                    ]
                },
                "gmake": {
                    "externals": [
                        {
                            "spec": "gmake@4.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "groff": {
                    "externals": [
                        {
                            "spec": "groff@1.22.4",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libtool": {
                    "externals": [
                        {
                            "spec": "libtool@2.4.6",
                            "prefix": "/usr",
                        }
                    ]
                },
                "libiconv": {
                    "externals": [
                        {
                            "spec": "libiconv@1.18",
                            "prefix": "/usr",
                        }
                    ]
                },
                "m4": {
                    "externals": [
                        {
                            "spec": "m4@1.4.19",
                            "prefix": "/usr",
                        }
                    ]
                },
                "openssh": {
                    "externals": [
                        {
                            "spec": "openssh@8.7p1",
                            "prefix": "/usr",
                        }
                    ]
                },
                "openssl": {
                    "externals": [
                        {
                            "spec": "openssl@3.2.2",
                            "prefix": "/usr",
                        }
                    ]
                },
                "perl": {
                    "externals": [
                        {
                            "spec": "perl@5.32.1~cpanm+opcode+open+shared+threads",
                            "prefix": "/usr",
                        }
                    ]
                },
                "pigz": {
                    "externals": [
                        {
                            "spec": "pigz@2.8",
                            "prefix": "/usr",
                        }
                    ],
                },
                "pkgconf": {
                    "externals": [
                        {
                            "spec": "pkgconf@1.7.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "python": {
                    "externals": [
                        {
                            "spec": "python@3.9.21+bz2+crypt+ctypes+dbm+lzma+pyexpat+pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib",
                            "prefix": "/usr",
                        }
                    ]
                },
                "sed": {
                    "externals": [
                        {
                            "spec": "sed@4.8",
                            "prefix": "/usr",
                        }
                    ]
                },
                "singularity": {
                    "externals": [
                        {
                            "spec": "singularity@4.3.3",
                            "prefix": "/usr",
                        }
                    ]
                },
                "slurm": {
                    "externals": [
                        {
                            "spec": "slurm@24.05.8",
                            "prefix": "/usr",
                        }
                    ]
                },
                "tar": {
                    "externals": [
                        {
                            "spec": "tar@1.34",
                            "prefix": "/usr",
                        }
                    ]
                },
                "xz": {
                    "externals": [
                        {
                            "spec": "xz@5.2.5",
                            "prefix": "/usr",
                        }
                    ]
                },
                "zlib": {
                    "externals": [
                        {
                            "spec": "zlib@1.2.11",
                            "prefix": "/usr",
                        }
                    ]
                },
                "zstd": {
                    "externals": [
                        {
                            "spec": "zstd@5.2.5",
                            "prefix": "/usr",
                        }
                    ]
                },
            }
        }
        if self.spec.satisfies("compiler=gcc") or self.spec.satisfies("compiler=cuda"):
            selections["packages"] |= {
                "openmpi": {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.7",
                            "prefix": "/usr/mpi/gcc/openmpi-4.1.7rc1",
                            "extra_attributes": {
                                "ldflags": "-L/usr/mpi/gcc/openmpi-4.1.7rc1/lib64 -lmpi"
                            },
                        },
                    ],
                },
            }
        if not self.spec.satisfies("compiler=cuda"):
            selections["packages"] |= self.cuda_config()["packages"]

        return selections

    def cuda_config(self):
        cuda_version = self.cuda_version
        if self.spec.satisfies("compiler=nvhpc"):
            return {
                "packages": {
                    "cuda": {
                        "externals": [
                            {
                                "spec": f"cuda@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/cuda/{cuda_version}",
                                "modules": [
                                    "system/qc-gh200",
                                    f"nvhpc/{self.nvhpc_version}",
                                ],
                            }
                        ],
                        "buildable": False,
                    },
                    "curand": {
                        "externals": [
                            {
                                "spec": f"curand@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cusparse": {
                        "externals": [
                            {
                                "spec": f"cusparse@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cublas": {
                        "externals": [
                            {
                                "spec": f"cublas@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cusolver": {
                        "externals": [
                            {
                                "spec": f"cusolver@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "cufft": {
                        "externals": [
                            {
                                "spec": f"cufft@{cuda_version}",
                                "prefix": f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/{cuda_version}",
                            }
                        ],
                        "buildable": False,
                    },
                    "openmpi": {
                        "buildable": True,
                        "version": ["4.1.7"],
                        "variants": "+cuda+cxx cuda_arch=90 fabrics=ucx schedulers=slurm",
                    },
                }
            }
        return {
            "packages": {
                "cuda": {
                    "externals": [
                        {
                            "spec": f"cuda@{self.cuda_version}",
                            "prefix": f"/usr/local/cuda-{self.cuda_version}",
                        },
                    ],
                },
            }
        }

    def compute_compilers_section(self):
        gcc_cfg = compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@11.5.0 languages:=c,c++,fortran",
                    "/usr/",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                )
            ],
        )
        if self.spec.satisfies("compiler=cuda"):
            cuda_cfg = compiler_section_for(
                "cuda",
                [
                    compiler_def(
                        f"cuda@{self.cuda_version}",
                        f"/usr/local/cuda-{self.cuda_version}",
                        {"c": "nvcc", "cxx": "nvcc"},
                    )
                ],
            )
            return merge_dicts(cuda_cfg, gcc_cfg)
        if self.spec.satisfies("compiler=nvhpc"):
            return compiler_section_for(
                "nvhpc",
                [
                    compiler_def(
                        f"nvhpc@{self.nvhpc_version}",
                        f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/compilers",
                        {"c": "nvc", "cxx": "nvc++", "fortran": "nvfortran"},
                        extra_rpaths=[
                            f"/opt/nvidia/hpc_sdk/Linux_aarch64/{self.nvhpc_version}/math_libs/lib64",
                        ],
                        modules=[
                            "system/qc-gh200",
                            f"nvhpc/{self.nvhpc_version}",
                        ],
                    )
                ],
            )
        return gcc_cfg

    def system_specific_variables(self):
        return {
            "cuda_arch": "90",
            "queue": "qc-gh200",
            "pre_exec_cmds": "export SLURM_MPI_TYPE=pmix",
        }

    def compute_software_section(self):
        default_comp = self.spec.variants["compiler"][0]
        return {
            "software": {
                "packages": {
                    "default-compiler": {"pkg_spec": f"{default_comp}"},
                    "default-mpi": {"pkg_spec": "openmpi"},
                    "compiler-gcc": {"pkg_spec": "gcc"},
                    "compiler-nvhpc": {"pkg_spec": "nvhpc"},
                    "cublas-cuda": {"pkg_spec": "cublas"},
                    "blas": {"pkg_spec": "openblas"},
                    "lapack": {"pkg_spec": "openblas"},
                }
            }
        }
