# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant, maintainers
from benchpark.system import System, JobQueue
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from benchpark.paths import hardware_descriptions


class LlnlCluster(System):

    maintainers("nhanford", "rfhaque")

    id_to_resources = {
        "ruby": {
            "sys_cores_per_node": 56,
            "sys_cores_os_reserved_per_node": 0,  # No core or thread reservation
            "sys_cores_os_reserved_per_node_list": None,
            "sys_mem_per_node_GB": 206,
            "sys_cpu_mem_per_node_MB": 77,
            "sys_cpu_L1_KB": 32,  # 32KB for L1d and 32KB for L1i
            "sys_cpu_L2_KB": 1024,
            "sys_cpu_L3_MB": 38.5,  # 38.5 MB
            "sys_sockets_per_node": 2,
            "system_site": "llnl",
            "hardware_key": str(hardware_descriptions)
            + "/Supermicro-icelake-OmniPath/hardware_description.yaml",
            "queues": [JobQueue("pdebug", 60, 12), JobQueue("pbatch", 1440, 520)],
        },
        "magma": {
            "sys_cores_per_node": 96,
            "system_site": "llnl",
            "hardware_key": str(hardware_descriptions)
            + "/Penguin-icelake-OmniPath/hardware_description.yaml",
            "queues": [JobQueue("pdebug", 60, 4), JobQueue("pbatch", 2160, 64)],
        },
        "dane": {
            "sys_cores_per_node": 112,
            "sys_cores_os_reserved_per_node": 0,  # No explicit core reservation, first thread on each core reserved (2 threads per core)
            "sys_cores_os_reserved_per_node_list": None,
            "sys_mem_per_node_GB": 256,
            "sys_cpu_mem_per_node_MB": 210,
            "sys_cpu_L1_KB": 48,  # 48KB for L1d and 32KB for L1i
            "sys_cpu_L2_KB": 2048,
            "sys_cpu_L3_MB": 105,  # 105MB
            "system_site": "llnl",
            "hardware_key": str(hardware_descriptions)
            + "/DELL-sapphirerapids-OmniPath/hardware_description.yaml",
            "queues": [JobQueue("pdebug", 60, 20), JobQueue("pbatch", 1440, 520)],
        },
    }

    variant(
        "cluster",
        default="dane",
        values=("ruby", "magma", "dane"),
        description="Which cluster to run on",
    )

    variant(
        "compiler",
        default="oneapi",
        values=("oneapi", "gcc", "intel"),
        description="Which compiler to use",
    )

    variant(
        "bank",
        default="none",
        values=("none", "guests", "asccasc", "lc", "fractale"),
        multi=False,
        description="Submit a job to a specific named bank",
    )

    variant(
        "queue",
        default="none",
        values=("none", "pbatch", "pdebug"),
        multi=False,
        description="Submit to queue other than the default queue (e.g. pdebug)",
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
                            "spec": "python@2.7.18+bz2+crypt+ctypes+dbm~lzma+pyexpat~pythoncmd+readline+sqlite3+ssl~tkinter+uuid+zlib",
                            "prefix": "/usr",
                        },
                        {
                            "spec": "python@3.6.8+bz2+crypt+ctypes+dbm+lzma+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib",
                            "prefix": "/usr",
                        },
                        {
                            "spec": "python@2.7.18+bz2+crypt+ctypes+dbm~lzma+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib",
                            "prefix": "/usr/tce",
                        },
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
        elif self.spec.satisfies("compiler=oneapi"):
            selections |= {
                "packages": selections["packages"]
                | {
                    "mpi": {
                        "buildable": False,
                        "externals": [
                            {
                                "spec": "mvapich2@2.3.7-intel202321",
                                "prefix": "/usr/tce/packages/mvapich2/mvapich2-2.3.7-intel-2023.2.1",
                                "extra_attributes": {
                                    "ldflags": "-L/usr/tce/packages/mvapich2/mvapich2-2.3.7-intel-2023.2.1/lib -lmpi"
                                },
                            }
                        ],
                    }
                }
            }

        selections["packages"] |= self.compiler_weighting_cfg()["packages"]

        return selections

    def compiler_weighting_cfg(self):
        if self.spec.satisfies("compiler=oneapi"):
            return {"packages": {"all": {"require": [{"one_of": ["%oneapi", "%gcc"]}]}}}
        else:
            return {"packages": {}}

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
        elif self.spec.satisfies("compiler=oneapi"):
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
                    },
                    {
                        "compiler": {
                            "spec": "oneapi@2023.2.1",
                            "paths": {
                                "cc": "/usr/tce/packages/intel/intel-2023.2.1/compiler/2023.2.1/linux/bin/icx",
                                "cxx": "/usr/tce/packages/intel/intel-2023.2.1/compiler/2023.2.1/linux/bin/icpx",
                                "f77": "/usr/tce/packages/intel/intel-2023.2.1/compiler/2023.2.1/linux/bin/ifx",
                                "fc": "/usr/tce/packages/intel/intel-2023.2.1/compiler/2023.2.1/linux/bin/ifx",
                            },
                            "flags": {},
                            "operating_system": "rhel8",
                            "target": "x86_64",
                            "modules": [],
                            "environment": {},
                            "extra_rpaths": [],
                        }
                    },
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
