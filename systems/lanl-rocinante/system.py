# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


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


class LanlRocinante(System):

    maintainers("sriram-LANL")

    id_to_resources = {
        "crossroads": {
            "sys_cores_per_node": 112,
            "sys_cores_os_reserved_per_node": 0,  # No core or thread reservation
            "sys_cores_os_reserved_per_node_list": None,
            "sys_mem_per_node_GB": 256,
            "sys_cpu_mem_per_node_MB": 210,
            "sys_cpu_L1_KB": 48,  # 48KB for L1d and 32KB for L1i
            "sys_cpu_L2_KB": 2048,
            "sys_cpu_L3_MB": 105,  # 105MB
            "system_site": "lanl",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-sapphirerapids-Slingshot/hardware_description.yaml",
            "queues": [
                JobQueue("debug", 60, 12),
                JobQueue("hbm", 60, 12),
                JobQueue("standard", 1440, 520),
            ],
        },
        "rocinante": {
            "sys_cores_per_node": 112,
            "sys_cores_os_reserved_per_node": 0,  # No core or thread reservation
            "sys_cores_os_reserved_per_node_list": None,
            "sys_mem_per_node_GB": 256,
            "sys_cpu_mem_per_node_MB": 210,
            "sys_cpu_L1_KB": 48,  # 48KB for L1d and 32KB for L1i
            "sys_cpu_L2_KB": 2048,
            "sys_cpu_L3_MB": 105,  # 105MB
            "system_site": "lanl",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-sapphirerapids-Slingshot/hardware_description.yaml",
            "queues": [
                JobQueue("debug", 60, 12),
                JobQueue("hbm", 60, 12),
                JobQueue("standard", 1440, 520),
            ],
        },
        "tycho": {
            "sys_cores_per_node": 112,
            "sys_cores_os_reserved_per_node": 0,  # No core or thread reservation
            "sys_cores_os_reserved_per_node_list": None,
            "sys_mem_per_node_GB": 256,
            "sys_cpu_mem_per_node_MB": 210,
            "sys_cpu_L1_KB": 48,  # 48KB for L1d and 32KB for L1i
            "sys_cpu_L2_KB": 2048,
            "sys_cpu_L3_MB": 105,  # 105MB
            "system_site": "lanl",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-sapphirerapids-Slingshot/hardware_description.yaml",
            "queues": [
                JobQueue("debug", 60, 12),
                JobQueue("hbm", 60, 12),
                JobQueue("standard", 1440, 520),
            ],
        },
    }

    variant(
        "cluster",
        default="rocinante",
        values=("rocinante", "tycho", "crossroads"),
        description="Which cluster to run on",
    )

    variant(
        "compiler",
        default="oneapi",
        values=("oneapi", "gcc"),
        description="Which compiler to use",
    )

    variant(
        "queues",
        default="standard",
        values=("standard", "hbm", "debug"),
        multi=False,
        description="Submit to queue other than the default queue (e.g. hbm)",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [OpenMPCPUOnlySystem()]

        self.scheduler = "slurm"
        attrs = self.id_to_resources.get(self.spec.variants["cluster"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):
        selections = {
            "packages": {
                "elfutils": {
                    "externals": [{"spec": "elfutils@0.185", "prefix": "/usr"}],
                    "buildable": False,
                },
                "papi": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "papi@7.0.1.2",
                            "prefix": "/cpe/23.12/papi/7.0.1.2",
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
                            "spec": "intel-oneapi-mkl@2023.2.0",
                            "prefix": "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/oneapi/2023.2.0.49397/mkl/2023.2.0",
                        }
                    ],
                },
                "libfabric": {
                    "externals": [
                        {
                            "spec": "libfabric@1.3",
                            "prefix": "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/oneapi/2023.2.0.49397/mpi/2021.10.0/libfabric/lib",
                        }
                    ],
                    "buildable": False,
                },
                "lapack": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "intel-oneapi-mkl@2023.2.0",
                            "prefix": "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/oneapi/2023.2.0.49397/mkl/2023.2.0",
                        }
                    ],
                },
                "fftw": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "fftw@3.3.10.6",
                            "prefix": "/cpe/23.12/fftw/3.3.10.6/x86_spr",
                        }
                    ],
                },
                "diffutils": {
                    "externals": [{"spec": "diffutils@3.6", "prefix": "/usr"}],
                    "buildable": False,
                },
                "cmake": {
                    "externals": [
                        {
                            "spec": "cmake@3.29.6",
                            "prefix": "/usr/projects/hpcsoft/tce/23.12/cos3-x86_64/packages/cmake/cmake-3.29.6",
                        },
                    ],
                    "buildable": False,
                },
                "tar": {
                    "externals": [{"spec": "tar@1.34", "prefix": "/usr"}],
                    "buildable": False,
                },
                "autoconf": {
                    "externals": [{"spec": "autoconf@2.69", "prefix": "/usr"}],
                    "buildable": False,
                },
                "python": {
                    "externals": [
                        {
                            "spec": "python@3.6.15",
                            "prefix": "/usr",
                        },
                        {
                            "spec": "python@3.11.5",
                            "prefix": "/cpe/23.12/python/3.11.5",
                        },
                        {
                            "spec": "python@3.13.9",
                            "prefix": "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/python/3.13.9",
                        },
                    ],
                    "buildable": False,
                },
                "gmake": {
                    "externals": [{"spec": "gmake@4.2.1", "prefix": "/usr"}],
                    "buildable": False,
                },
            }
        }

        if self.spec.satisfies("compiler=gcc"):
            base_mpich_gcc = "/cpe/23.12/mpich/8.1.28/ofi/gnu/12.3"
            # base_openmpi_gcc = "/usr/projects/hpcsoft/tce/23.12/cos3-x86_64/packages/openmpi/openmpi-5.0.6-gcc-12.3.0"
            selections["packages"] |= {
                "mpich": {
                    "externals": [
                        {
                            "spec": "cray-mpich@8.1.28",
                            "prefix": base_mpich_gcc,
                            "extra_attributes": {
                                "ldflags": f"-L{base_mpich_gcc}/lib -lmpi"
                            },
                        },
                    ],
                },
            }
        elif self.spec.satisfies("compiler=oneapi"):
            base_mpich_oneapi = "/cpe/23.12/mpich/8.1.28/ofi/intel/2022.1"
            selections["packages"] |= {
                "mpi": {
                    "buildable": False,
                },
                "mpich": {
                    "externals": [
                        {
                            "spec": "mpich@3.4a2~hydra device=ch4 netmod=ofi",
                            "prefix": base_mpich_oneapi,
                            "extra_attributes": {
                                "ldflags": f"-L{base_mpich_oneapi}/lib -lmpi"
                            },
                        }
                    ],
                },
            }

        return selections

    def compute_compilers_section(self):
        gcc_cfg = compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@12.3.0",
                    "/usr/projects/hpcsoft/tce/23.12/cos3-x86_64/compilers/gcc/12.3.0",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                )
            ],
        )
        if self.spec.satisfies("compiler=gcc"):
            cfg = gcc_cfg
        elif self.spec.satisfies("compiler=oneapi"):
            oneapi_cfg = compiler_section_for(
                "intel-oneapi-compilers",
                [
                    compiler_def(
                        "intel-oneapi-compilers@2023.2.0 ~envmods",
                        "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/oneapi/2023.2.0.49397/compiler/2023.2.0/linux",
                        {"c": "icx", "cxx": "icpx", "fortran": "ifx"},
                        env={
                            "prepend_path": {
                                "LD_LIBRARY_PATH": "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/oneapi/2023.2.0.49397/mpi/2021.10.0/libfabric/lib:/cpe/23.12/pmi/6.1.13/lib",
                            },
                        },
                    ),
                ],
            )
            prefs = {"one_of": ["intel-oneapi-compilers", "gcc"]}
            weighting_cfg = {
                "packages": {
                    "c": {"require": [prefs]},
                    "cxx": {"require": [prefs]},
                    "fortran": {"require": [prefs]},
                }
            }
            cfg = merge_dicts(gcc_cfg, oneapi_cfg, weighting_cfg)

        return cfg

    def compute_software_section(self):
        if self.spec.satisfies("compiler=oneapi"):
            default_compiler = "intel-oneapi-compilers"
        else:
            default_compiler = "gcc"

        return {
            "software": {
                "packages": {
                    "default-compiler": {"pkg_spec": default_compiler},
                    "default-mpi": {"pkg_spec": "mpich"},
                    "compiler-gcc": {"pkg_spec": "gcc"},
                    "mpi-gcc": {"pkg_spec": "openmpi"},
                    "compiler-oneapi": {"pkg_spec": "oneapi"},
                    "mpi-oneapi": {"pkg_spec": "mpich"},
                    "blas": {"pkg_spec": "intel-oneapi-mkl"},
                    "lapack": {"pkg_spec": "intel-oneapi-mkl"},
                }
            }
        }
