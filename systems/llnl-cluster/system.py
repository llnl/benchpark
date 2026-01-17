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
            "mount_points": ["/l/ssd", "/p/lustre1", "/p/lustre2", "/p/lustre3"],
        },
        "magma": {
            "sys_cores_per_node": 96,
            "system_site": "llnl",
            "hardware_key": str(hardware_descriptions)
            + "/Penguin-icelake-OmniPath/hardware_description.yaml",
            "queues": [JobQueue("pdebug", 60, 4), JobQueue("pbatch", 2160, 64)],
            "mount_points": ["/l/ssd", "/p/lustre1", "/p/lustre2", "/p/lustre3"],
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
            "mount_points": ["/l/ssd", "/p/lustre1", "/p/lustre2", "/p/lustre3"],
        },
        "rzgenie": {
            "sys_cores_per_node": 36,
            "system_site": "llnl",
            "sys_sockets_per_node": 2,
            "sys_cpu_L2_KB": 256,
            "sys_cpu_L3_MB": 45,
            "hardware_key": str(hardware_descriptions)
            + "/Penguin-haswell-OmniPath/hardware_description.yaml",
            "queues": [JobQueue("pdebug", 720, 43)],
            "mount_points": ["/l/ssd", "/p/lustre1", "/p/lustre2", "/p/lustre3"],
        },
        "poodle": {
            "sys_cores_per_node": 112,
            "sys_sockets_per_node": 2,
            "sys_cpu_L2_KB": 2048,
            "sys_cpu_L3_MB": 112.5,  # Depends on partition (could be 105)
            "system_site": "llnl",
            "hardware_key": str(hardware_descriptions)
            + "/DELL-sapphirerapids-OmniPath/hardware_description.yaml",
            "queues": [
                JobQueue("pdebug", 30, 3),
                JobQueue("pbatch", 12000, 29),
                JobQueue("phighmem", 12000, 4),
            ],
            "mount_points": ["/l/ssd", "/p/lustre1", "/p/lustre2", "/p/lustre3"],
        },
    }

    variant(
        "cluster",
        default="dane",
        values=("ruby", "magma", "dane", "rzgenie", "poodle"),
        description="Which cluster to run on",
    )

    variant(
        "compiler",
        default="oneapi",
        values=("oneapi", "gcc", "intel", "clang"),
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

    variant(
        "queue",
        default="none",
        values=("none", "pbatch", "pdebug", "phighmem"),
        multi=False,
        description="Submit to queue other than the default queue (e.g. pdebug)",
    )

    variant(
        "mount_point",
        default="none",
        values=("none", "l/ssd", "/p/lustre1", "/p/lustre2", "/p/lustre3"),
        multi=False,
        description="Which mount point to use for IO benchmarks",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [OpenMPCPUOnlySystem()]

        self.scheduler = "slurm"
        attrs = self.id_to_resources.get(self.spec.variants["cluster"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

        mount_point = self.spec.variants["mount_point"][0]
        if mount_point not in self.mount_points + ["none"]:
            raise KeyError(
                f'"{mount_point}" is not a valid mount point for the cluster "{self.spec.variants["cluster"][0]}"'
            )
        if mount_point == "none":
            self.full_io_path = None
        else:
            self.full_io_path = mount_point + "/$USER/test.bat"

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
                "automake": {
                    "externals": [{"spec": "automake@1.16.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "libtool": {
                    "externals": [{"spec": "libtool@2.4.6", "prefix": "/usr"}],
                    "buildable": False,
                },
                "ncurses": {
                    "externals": [{"spec": "ncurses@6.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "m4": {
                    "externals": [{"spec": "m4@1.4.18", "prefix": "/usr"}],
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
                            "prefix": "/usr/tce/packages/mvapich2/mvapich2-2.3.7-gcc-13.3.1",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/mvapich2/mvapich2-2.3.7-gcc-13.3.1/lib -lmpi"
                            },
                        }
                    ],
                }
            elif mpi_type == "openmpi":
                mpi_dict["openmpi"] = {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.2",
                            "prefix": "/usr/tce/packages/openmpi/openmpi-4.1.2-gcc-13.3.1",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/openmpi/openmpi-4.1.2-gcc-13.3.1/lib -lmpi"
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
                            "prefix": "/usr/tce/packages/mvapich2/mvapich2-2.3.7-intel-2025.2.0",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/mvapich2/mvapich2-2.3.7-intel-2025.2.0/lib -lmpi"
                            },
                        }
                    ],
                }
            elif mpi_type == "openmpi":
                mpi_dict["openmpi"] = {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.2",
                            "prefix": "/usr/tce/packages/openmpi/openmpi-4.1.2-intel-2025.2.0",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/openmpi/openmpi-4.1.2-intel-2025.2.0/lib -lmpi"
                            },
                        }
                    ],
                }
        elif self.spec.satisfies("compiler=clang"):
            if mpi_type == "mvapich2":
                mpi_dict["mvapich2"] = {
                    "externals": [
                        {
                            "spec": "mvapich2@2.3.7",
                            "prefix": "/usr/tce/packages/mvapich2/mvapich2-2.3.7-clang-19.1.3",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/mvapich2/mvapich2-2.3.7-clang-19.1.3/lib -lmpi"
                            },
                        }
                    ],
                }
            elif mpi_type == "openmpi":
                mpi_dict["openmpi"] = {
                    "externals": [
                        {
                            "spec": "openmpi@4.1.2",
                            "prefix": "/usr/tce/packages/openmpi/openmpi-4.1.2-clang-19.1.3",
                            "extra_attributes": {
                                "ldflags": "-L/usr/tce/packages/openmpi/openmpi-4.1.2-clang-19.1.3/lib -lmpi"
                            },
                        }
                    ],
                }

        selections |= {"packages": selections["packages"] | mpi_dict}

        return selections

    def compute_compilers_section(self):
        if self.spec.satisfies("compiler=gcc"):
            cfg = compiler_section_for(
                "gcc",
                [
                    compiler_def(
                        "gcc@13.3.1 languages:=c,c++,fortran",
                        "/usr/tce/packages/gcc/gcc-13.3.1/",
                        {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                    )
                ],
            )
        elif self.spec.satisfies("compiler=intel"):
            cfg = compiler_section_for(
                "intel-oneapi-compilers-classic",
                [
                    compiler_def(
                        "intel-oneapi-compilers-classic@2021.6.0~envmods",
                        "/usr/tce/packages/intel-classic/intel-classic-2021.6.0/",
                        {"c": "icc", "cxx": "icpc", "fortran": "ifort"},
                    )
                ],
            )
        elif self.spec.satisfies("compiler=oneapi"):
            gcc_cfg = compiler_section_for(
                "gcc",
                [
                    compiler_def(
                        "gcc@13.3.1",
                        "/usr/tce/packages/gcc/gcc-13.3.1/",
                        {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                    )
                ],
            )
            oneapi_cfg = compiler_section_for(
                "intel-oneapi-compilers",
                [
                    compiler_def(
                        "intel-oneapi-compilers@2025.2.0~envmods",
                        "/usr/tce/packages/intel/intel-2025.2.0/compiler/2025.2/",
                        {"c": "icx", "cxx": "icpx", "fortran": "ifx"},
                    )
                ],
            )
            prefs = {"one_of": ["%oneapi", "%gcc"], "when": "%c"}
            weighting_cfg = {"packages": {"all": {"require": [prefs]}}}
            cfg = merge_dicts(gcc_cfg, oneapi_cfg, weighting_cfg)
        elif self.spec.satisfies("compiler=clang"):
            cfg = compiler_section_for(
                "clang",
                [
                    compiler_def(
                        "clang@19.1.3",
                        "/usr/tce/packages/clang/clang-19.1.3/",
                        {"c": "clang", "cxx": "clang++", "fortran": "flang-new"},
                    )
                ],
            )

        return cfg

    def compute_software_section(self):
        default_compiler = "gcc"
        if self.spec.satisfies("compiler=intel"):
            default_compiler = "intel-oneapi-compilers-classic"
        elif self.spec.satisfies("compiler=oneapi"):
            default_compiler = "intel-oneapi-compilers"
        elif self.spec.satisfies("compiler=clang"):
            default_compiler = "clang"

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
