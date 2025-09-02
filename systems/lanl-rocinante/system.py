# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant, maintainers
from benchpark.system import System, JobQueue
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from benchpark.paths import hardware_descriptions


class LanlCTS2(System):

    maintainers("sriram")

    id_to_resources = {
        "rocinante": {
            "sys_cores_per_node": 112,
            "sys_cores_os_reserved_per_node": 0,  # No core or thread reservation
            "sys_cores_os_reserved_per_node_list": None,
            "system_site": "lanl",
            "hardware_key": str(hardware_descriptions)
            + "HPECray-sapphirerapids-Slingshot/hardware_description.yaml",
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
        values=("oneapi"),
        description="Which compiler to use",
    )

    variant(
        "queue",
        default="dev",
        values=("standard", "dev", "debug"),
        multi=False,
        description="Submit to queue other than the default queue (e.g. dev)",
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
                            "prefix": "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/oneapi/2023.2.0.49397/mkl/2023.2.0"
                        }
                    ],
                },
                "lapack": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "intel-oneapi-mkl@2023.2.0",
                            "prefix": "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/oneapi/2023.2.0.49397/mkl/2023.2.0"
                        }
                    ],
                },
                "fftw": {
                    "buildable": False,
                    "externals": [
                        {
                            "spec": "fftw@3.3.10.6",
                            "prefix": "/cpe/23.12/fftw/3.3.10.6/x86_spr"
                        }
                    ],
                },
                "diffutils": {
                    "externals": [{"spec": "diffutils@3.6", "prefix": "/usr"}],
                    "buildable": False,
                },
                "cmake": {
                    "externals": [
                        {"spec": "cmake@3.20.4", "prefix": "/usr"},
                        {"spec": "cmake@3.29.6", "prefix": "/usr/projects/hpcsoft/tce/23.12/cos3-x86_64/packages/cmake/cmake-3.29.6"},
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
                    ],
                    "buildable": False,
                },
                "hwloc": {
                    "externals": [
                        {"spec": "hwloc@2.9.0", "prefix": "/usr"},
                        {"spec": "hwloc@2.12.2", "prefix": "/users/sriram/software/hwloc-i23-mpich8"}
                    ],
                    "buildable": False,
                },
                "gmake": {
                    "externals": [{"spec": "gmake@4.2.1", "prefix": "/usr"}],
                    "buildable": False,
                },
            }
        }

        if self.spec.satisfies("compiler=oneapi"):
            selections |= {
                "packages": selections["packages"]
                | {
                    "mpi": {
                        "buildable": False,
                        "externals": [
                            {
                                "spec": "cray-mpich@8.1.28"
                                "prefix": "/cpe/23.12/mpich/8.1.28/ofi/intel/2022.1"
                                "extra_attributes": {
                                    "ldflags": "-L/cpe/23.12/mpich/8.1.28/ofi/intel/2022.1/lib -lmpi"
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
            return {"packages": {"all": {"require": [{"one_of": ["%oneapi"]}]}}}
        else:
            return {"packages": {}}

    def compute_compilers_section(self):
        selections = {}
        if self.spec.satisfies("compiler=oneapi"):
            selections = {
                "compilers": [
                    {
                        "compiler": {
                            "spec": "gcc@12.1.1",
                            "paths": {
                                "cxx": "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/oneapi/2023.2.0.49397/compiler/2023.2.0/linux/bin/icpx",
                                "cc": "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/oneapi/2023.2.0.49397/compiler/2023.2.0/linux/bin/icx",
                                "f77": "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/oneapi/2023.2.0.49397/compiler/2023.2.0/linux/bin/ifx",
                                "fc": "/usr/projects/hpcsoft/pe/installs/cos3-x86_64/oneapi/2023.2.0.49397/compiler/2023.2.0/linux/bin/ifx",
                            },
                            "flags": {},
                            "operating_system": "sles15",
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
                    "default-mpi": {"pkg_spec": "cray-mpich"},
                    "compiler-oneapi": {"pkg_spec": "oneapi"},
                    "blas": {"pkg_spec": "intel-oneapi-mkl"},
                    "lapack": {"pkg_spec": "intel-oneapi-mkl"},
                    "mpi-intel": {"pkg_spec": "cray-mpich"},
                }
            }
        }
