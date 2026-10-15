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


class JcahpcMiyabiG(System):
    """JCAHPC Miyabi-G (University of Tokyo / University of Tsukuba).

    Miyabi-G is the GPU partition of the Miyabi supercomputer.  Each compute
    node is a single NVIDIA GH200 Grace Hopper Superchip: a 72-core Arm
    Neoverse-V2 "Grace" CPU (120 GB LPDDR5X) tightly coupled to an H100
    "Hopper" GPU (96 GB HBM3).  The nodes are interconnected with NVIDIA
    InfiniBand and scheduled with PBS Professional.  The software stack is
    delivered through the JCAHPC "LNG" environment-modules tree rooted at
    ``/work/opt/local``; the NVIDIA HPC SDK (module ``nvidia/<ver>``) is the
    native toolchain and it ships HPC-X (OpenMPI) as ``nv-hpcx/<ver>``.
    """

    maintainers("yoshifuminakamura")

    # Verified against the live login node (miyabi-g1) on 2026-07-06:
    #   NVHPC root : /work/opt/local/aarch64/cores/nvidia/<ver>/Linux_aarch64/<ver>
    #   HPC-X MPI  : <nvhpc-root>/comm_libs/<cuda>/hpcx/latest/ompi
    #   Std. CUDA  : /work/opt/local/aarch64/cores/cuda/<ver>
    id_to_resources = {
        "miyabi-g": {
            "cuda_arch": "90",
            "pbs_emit_gpus": 0,
            "pbs_min_ncpus_per_node": 2,
            "sys_cores_per_node": 72,
            "sys_gpus_per_node": 1,
            "sys_mem_per_node_GB": 120,
            "system_site": "jcahpc",
            "hardware_key": str(hardware_descriptions)
            + "/NVIDIA-neoverse-GH200-Infiniband/hardware_description.yaml",
            # Elapse limits (minutes) / max nodes per Miyabi-G resource group.
            # Source: https://www.cc.u-tokyo.ac.jp/supercomputer/miyabi/service/job.php
            "queues": [
                JobQueue("debug-g", 30, 16),
                JobQueue("short-g", 480, 8),
                JobQueue("small-g", 2880, 16),
                JobQueue("medium-g", 2880, 64),
                JobQueue("large-g", 2880, 128),
                JobQueue("x-large-g", 1440, 256),
                JobQueue("interact-g", 120, 8),
                JobQueue("coupler-g", 2880, 128),
            ],
        },
    }

    variant(
        "compiler",
        default="nvhpc",
        values=("nvhpc", "gcc", "cuda"),
        description="Which compiler to use",
    )
    variant(
        "nvhpc",
        default="25.9",
        values=(
            "24.5",
            "24.9",
            "24.11",
            "25.1",
            "25.3",
            "25.5",
            "25.9",
            "25.11",
            "26.3",
        ),
        description="NVIDIA HPC SDK version",
    )
    variant(
        "cuda",
        default="12.6",
        values=("11.8", "12.4", "12.6", "12.8", "12.9", "13.2"),
        description="Standalone CUDA Toolkit version (used with compiler=gcc/cuda)",
    )
    variant(
        "queue",
        default="small-g",
        values=(
            "none",
            "debug-g",
            "short-g",
            "small-g",
            "medium-g",
            "large-g",
            "x-large-g",
            "interact-g",
            "coupler-g",
        ),
        multi=False,
        description="Submit to PBS resource group (queue)",
    )
    variant(
        "group",
        default="none",
        multi=False,
        description=(
            "JCAHPC project/group code for accounting, emitted as "
            "'#PBS -W group_list=<group>' (e.g. group=gz00). Required to "
            "actually submit a job; 'none' omits the directive."
        ),
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [CudaSystem(), OpenMPCPUOnlySystem()]
        self.scheduler = "pbs"

        self.nvhpc_version = Version(self.spec.variants["nvhpc"][0])
        self.cuda_version = Version(self.spec.variants["cuda"][0])

        if str(self.nvhpc_version) == "24.5":
            self.nvhpc_cuda_version = "12.4"
            self.hpcx_ompi_version = "4.1.7"
        if str(self.nvhpc_version) == "24.9":
            self.nvhpc_cuda_version = "12.6"
            self.hpcx_ompi_version = "4.1.7"
        if str(self.nvhpc_version) == "24.11":
            self.nvhpc_cuda_version = "12.6"
            self.hpcx_ompi_version = "4.1.7"
        if str(self.nvhpc_version) == "25.1":
            self.nvhpc_cuda_version = "12.6"
            self.hpcx_ompi_version = "4.1.7"
        if str(self.nvhpc_version) == "25.3":
            self.nvhpc_cuda_version = "12.8"
            self.hpcx_ompi_version = "4.1.7"
        if str(self.nvhpc_version) == "25.5":
            self.nvhpc_cuda_version = "12.9"
            self.hpcx_ompi_version = "4.1.9"
        if str(self.nvhpc_version) == "25.9":
            self.nvhpc_cuda_version = "13.0"
            self.hpcx_ompi_version = "4.1.9"
        if str(self.nvhpc_version) == "25.11":
            self.nvhpc_cuda_version = "13.0"
            self.hpcx_ompi_version = "4.1.9"
        if str(self.nvhpc_version) == "26.3":
            self.nvhpc_cuda_version = "13.1"
            self.hpcx_ompi_version = "4.1.9"

        # HPC-X (OpenMPI) is the vendor MPI on Miyabi-G. It is always sourced
        # from the NVIDIA HPC SDK bundle, even when building with gcc.
        self.nvhpc_base = (
            f"/work/opt/local/aarch64/cores/nvidia/{self.nvhpc_version}"
            f"/Linux_aarch64/{self.nvhpc_version}"
        )
        self.hpcx_prefix = (
            f"{self.nvhpc_base}/comm_libs/{self.nvhpc_cuda_version}/hpcx/latest/ompi"
        )

        # Effective CUDA: the HPC SDK bundle when building with nvhpc,
        # otherwise the standalone cuda module chosen by the `cuda` variant.
        if self.spec.satisfies("compiler=nvhpc"):
            self.cuda_version = self.nvhpc_cuda_version

        attrs = self.id_to_resources.get("miyabi-g")
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):
        selections = {
            "packages": {
                "all": {
                    "providers": {
                        "mpi": ["openmpi"],
                        "blas": ["openblas"],
                        "lapack": ["openblas"],
                        "scalapack": ["netlib-scalapack"],
                        "fftw-api": ["fftw"],
                    },
                    "permissions": {"write": "group"},
                },
                # Pre-installed OS tools (RHEL 9.4, aarch64). Versions verified
                # via rpm on the login node so Spack treats them as externals.
                "autoconf": {
                    "externals": [{"spec": "autoconf@2.69", "prefix": "/usr"}]
                },
                "automake": {
                    "externals": [{"spec": "automake@1.16.2", "prefix": "/usr"}]
                },
                "binutils": {
                    "externals": [
                        {"spec": "binutils@2.35.2~gold~headers", "prefix": "/usr"}
                    ]
                },
                "bison": {"externals": [{"spec": "bison@3.7.4", "prefix": "/usr"}]},
                "bzip2": {"externals": [{"spec": "bzip2@1.0.8", "prefix": "/usr"}]},
                "cmake": {"externals": [{"spec": "cmake@3.26.5", "prefix": "/usr"}]},
                "coreutils": {
                    "externals": [{"spec": "coreutils@8.32", "prefix": "/usr"}]
                },
                "diffutils": {
                    "externals": [{"spec": "diffutils@3.7", "prefix": "/usr"}]
                },
                "findutils": {
                    "externals": [{"spec": "findutils@4.8.0", "prefix": "/usr"}]
                },
                "flex": {"externals": [{"spec": "flex@2.6.4+lex", "prefix": "/usr"}]},
                "gawk": {"externals": [{"spec": "gawk@5.1.0", "prefix": "/usr"}]},
                "gettext": {"externals": [{"spec": "gettext@0.21", "prefix": "/usr"}]},
                "git": {"externals": [{"spec": "git@2.47.3~tcltk", "prefix": "/usr"}]},
                "gmake": {"externals": [{"spec": "gmake@4.3", "prefix": "/usr"}]},
                "libtool": {"externals": [{"spec": "libtool@2.4.6", "prefix": "/usr"}]},
                "m4": {"externals": [{"spec": "m4@1.4.19", "prefix": "/usr"}]},
                "ncurses": {
                    "externals": [
                        {"spec": "ncurses@6.2+termlib abi=6", "prefix": "/usr"}
                    ]
                },
                "openssl": {"externals": [{"spec": "openssl@3.5.5", "prefix": "/usr"}]},
                "perl": {
                    "externals": [
                        {
                            "spec": "perl@5.32.1~cpanm+opcode+open+shared+threads",
                            "prefix": "/usr",
                        }
                    ]
                },
                "pkgconf": {"externals": [{"spec": "pkgconf@1.7.3", "prefix": "/usr"}]},
                "python": {
                    "externals": [
                        {
                            "spec": "python@3.9.25+bz2+crypt+ctypes+dbm+lzma+pyexpat+pythoncmd+readline+sqlite3+ssl+tkinter+uuid+zlib",
                            "prefix": "/usr",
                        }
                    ]
                },
                "sed": {"externals": [{"spec": "sed@4.8", "prefix": "/usr"}]},
                "tar": {"externals": [{"spec": "tar@1.34", "prefix": "/usr"}]},
                "xz": {"externals": [{"spec": "xz@5.2.5", "prefix": "/usr"}]},
                "zlib": {"externals": [{"spec": "zlib@1.2.11", "prefix": "/usr"}]},
                # Vendor MPI: HPC-X (OpenMPI), CUDA-aware, from the HPC SDK.
                "openmpi": {
                    "externals": [
                        {
                            "spec": f"openmpi@{self.hpcx_ompi_version}+cuda",
                            "prefix": self.hpcx_prefix,
                            "modules": [
                                f"nvidia/{self.nvhpc_version}",
                                f"nv-hpcx/{self.nvhpc_version}",
                            ],
                        }
                    ],
                    "buildable": False,
                },
            }
        }
        # When compiler=cuda, CUDA is registered through the compilers section
        # instead; adding it here as well would double-define the `cuda`
        # package and collide during config merge.
        if not self.spec.satisfies("compiler=cuda"):
            selections["packages"] |= self.cuda_config()["packages"]
        return selections

    def cuda_config(self):
        cuda_version = self.cuda_version
        if self.spec.satisfies("compiler=nvhpc"):
            # CUDA + math libraries shipped inside the NVIDIA HPC SDK.
            math_libs = f"{self.nvhpc_base}/math_libs/{cuda_version}"
            modules = [f"nvidia/{self.nvhpc_version}"]
            math_pkgs = {
                lib: {
                    "externals": [
                        {
                            "spec": f"{lib}@{cuda_version}",
                            "prefix": math_libs,
                            "modules": modules,
                        }
                    ],
                    "buildable": False,
                }
                for lib in ("curand", "cusparse", "cublas", "cusolver", "cufft")
            }
            return {
                "packages": {
                    "cuda": {
                        "externals": [
                            {
                                "spec": f"cuda@{cuda_version}",
                                "prefix": f"{self.nvhpc_base}/cuda/{cuda_version}",
                                "modules": modules,
                            }
                        ],
                        "buildable": False,
                    },
                    **math_pkgs,
                }
            }

        # compiler=gcc or compiler=cuda: use the standalone CUDA Toolkit module.
        prefix = f"/work/opt/local/aarch64/cores/cuda/{cuda_version}"
        modules = [f"cuda/{cuda_version}"]
        return {
            "packages": {
                "cuda": {
                    "externals": [
                        {
                            "spec": f"cuda@{cuda_version}",
                            "prefix": prefix,
                            "modules": modules,
                        }
                    ],
                    "buildable": False,
                },
            }
        }

    def compute_compilers_section(self):
        gcc_cfg = compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@11.4.1 languages:=c,c++,fortran",
                    "/usr",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                )
            ],
        )
        if self.spec.satisfies("compiler=nvhpc"):
            nvhpc_cfg = compiler_section_for(
                "nvhpc",
                [
                    compiler_def(
                        f"nvhpc@{self.nvhpc_version}",
                        f"{self.nvhpc_base}/compilers",
                        {"c": "nvc", "cxx": "nvc++", "fortran": "nvfortran"},
                        extra_rpaths=[f"{self.nvhpc_base}/math_libs/lib64"],
                        modules=[f"nvidia/{self.nvhpc_version}"],
                    )
                ],
            )
            return merge_dicts(nvhpc_cfg, gcc_cfg)
        if self.spec.satisfies("compiler=cuda"):
            cuda_cfg = compiler_section_for(
                "cuda",
                [
                    compiler_def(
                        f"cuda@{self.cuda_version}",
                        f"/work/opt/local/aarch64/cores/cuda/{self.cuda_version}",
                        {"c": "nvcc", "cxx": "nvcc"},
                        modules=[f"cuda/{self.cuda_version}"],
                    )
                ],
            )
            return merge_dicts(cuda_cfg, gcc_cfg)
        return gcc_cfg

    def system_specific_variables(self):
        variables = {
            "cuda_arch": self.cuda_arch,
            # Avoid too-small PBS cpusets that make HPC-X/Open MPI hwloc fail
            # during startup on Miyabi-G.
            "pbs_emit_gpus": self.pbs_emit_gpus,
            "pbs_min_ncpus_per_node": self.pbs_min_ncpus_per_node,
        }
        # JCAHPC PBS requires the project group via `-W group_list=<group>`
        # (not `-A`). Inject it as an extra batch directive when provided.
        group = self.spec.variants["group"][0]
        if group != "none":
            variables["extra_batch_opts"] = f"-W group_list={group}"
        return variables

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
