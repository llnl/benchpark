# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from packaging.version import Version

from benchpark.cudasystem import CudaSystem
from benchpark.directives import maintainers, variant
from benchpark.paths import hardware_descriptions
from benchpark.system import System, compiler_def, compiler_section_for, merge_dicts


class CscsDaint(System):

    maintainers("pearce8")

    id_to_resources = {
        "daint": {
            "sys_cores_per_node": 12,
            "sys_gpus_per_node": 1,
            "sys_mem_per_node_GB": 64,
            "system_site": "cscs",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-haswell-P100-Infiniband/hardware_description.yaml",
        }
    }

    variant(
        "cuda",
        default="11.2.0",
        values=("11.2.0", "11.1.0", "11.0.207", "10.2.89"),
        description="CUDA version",
    )
    variant(
        "gtl",
        default=False,
        values=(True, False),
        description="Use GTL-enabled MPI",
    )
    variant(
        "compiler",
        default="cce",
        values=("gcc9", "gcc10", "gcc11", "cce", "intel", "pgi", "nvhpc"),
        description="Which compiler to use",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [CudaSystem()]
        self.cuda_arch = 60
        self.cuda_version = Version(self.spec.variants["cuda"][0])
        self.gtl_flag = self.spec.variants["gtl"][0]

        full_versions = {
            "cce": "12.0.3",
            "gcc9": "9.3.0",
            "gcc10": "10.3.0",
            "gcc11": "11.2.0",
            "intel": "2021.3.0",
            "nvhpc": "21.3",
        }
        for key, value in full_versions.items():
            if key == self.spec.variants["compiler"][0]:
                self.compiler_version = Version(value)

        self.scheduler = "slurm"
        attrs = self.id_to_resources.get("daint")
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):
        selections = self.cuda_config(self.cuda_version)
        return selections | {
            "packages": selections["packages"]
            | {
                "all": {
                    "providers": {
                        "mpi": ["cray-mpich"],
                        "pkgconfig": ["pkg-config", "pkgconf"],
                    }
                },
                "pkg-config": {
                    "externals": [{"spec": "pkg-config@0.29.2", "prefix": "/usr"}]
                },
                "r": {
                    "externals": [{"spec": "r@4.1.1.0", "modules": ["cray-R/4.1.1.0"]}]
                },
                "jemalloc": {
                    "externals": [
                        {
                            "spec": "jemalloc@5.1.0.3",
                            "modules": ["cray-jemalloc/5.1.0.3"],
                        }
                    ]
                },
                "cray-libsci": {
                    "externals": [
                        {
                            "spec": "cray-libsci@20.09.1",
                            "modules": ["cray-libsci/20.09.1"],
                        }
                    ]
                },
                "cray-mpich": {
                    "externals": [
                        {"spec": "cray-mpich@7.7.18", "modules": ["cray-mpich/7.7.18"]}
                    ]
                },
                "netcdf-c": {
                    "externals": [
                        {
                            "spec": "netcdf-c@4.7.4.4+mpi+parallel-netcdf",
                            "modules": ["cray-netcdf-hdf5parallel/4.7.4.4"],
                        }
                    ]
                },
                "petsc": {
                    "externals": [
                        {
                            "spec": "petsc@3.14.5.0~complex~cuda~int64",
                            "modules": ["cray-petsc/3.14.5.0"],
                        },
                        {
                            "spec": "petsc@3.14.5.0~complex~cuda+int64",
                            "modules": ["cray-petsc-64/3.14.5.0"],
                        },
                        {
                            "spec": "petsc@3.14.5.0+complex~cuda~int64",
                            "modules": ["cray-petsc-complex/3.14.5.0"],
                        },
                        {
                            "spec": "petsc@3.14.5.0+complex~cuda+int64",
                            "modules": ["cray-petsc-complex-64/3.14.5.0"],
                        },
                    ]
                },
                "papi": {
                    "externals": [{"spec": "papi@6.0.0.9", "modules": ["papi/6.0.0.9"]}]
                },
            }
        }

    def compute_compilers_section(self):
        compiler_map = {}
        compiler_map["cce"] = compiler_section_for(
            "cce",
            [
                compiler_def(
                    "cce@12.0.3",
                    "/path/is/now/needed/",  # <-- TODO: this needs to be filled in
                    {"c": "cc", "cxx": "CC", "fortran": "ftn"},
                    modules=["PrgEnv-cray", "cce/12.0.3"],
                    compilers_use_relative_paths=True,
                )
            ],
        )
        compiler_map["gcc9"] = compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@9.3.0 languages:=c,c++,fortran",
                    "/path/is/now/needed/",  # <-- TODO: this needs to be filled in
                    {"c": "cc", "cxx": "CC", "fortran": "ftn"},
                    modules=["PrgEnv-gnu", "gcc/9.3.0"],
                    compilers_use_relative_paths=True,
                )
            ],
        )
        compiler_map["gcc10"] = compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@10.3.0 languages:=c,c++,fortran",
                    "/path/is/now/needed/",  # <-- TODO: this needs to be filled in
                    {"c": "cc", "cxx": "CC", "fortran": "ftn"},
                    modules=["PrgEnv-gnu", "gcc/10.3.0"],
                    compilers_use_relative_paths=True,
                )
            ],
        )
        compiler_map["gcc11"] = compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@11.2.0 languages:=c,c++,fortran",
                    "/path/is/now/needed/",  # <-- TODO: this needs to be filled in
                    {"c": "cc", "cxx": "CC", "fortran": "ftn"},
                    modules=["PrgEnv-gnu", "gcc/11.2.0"],
                    compilers_use_relative_paths=True,
                )
            ],
        )
        compiler_map["intel"] = compiler_section_for(
            "intel-oneapi-compilers",
            [
                compiler_def(
                    "intel-oneapi-compilers@2021.3.0",
                    "/path/is/now/needed/",  # <-- TODO: this needs to be filled in
                    {"c": "cc", "cxx": "CC", "fortran": "ftn"},
                    modules=["PrgEnv-intel", "intel/2021.3.0"],
                    compilers_use_relative_paths=True,
                )
            ],
        )
        compiler_map["pgi"] = compiler_section_for(
            "pgi",
            [
                compiler_def(
                    "pgi@20.1.1",
                    "/path/is/now/needed/",  # <-- TODO: this needs to be filled in
                    {"c": "cc", "cxx": "CC", "fortran": "ftn"},
                    modules=["PrgEnv-pgi", "pgi/20.1.1"],
                    compilers_use_relative_paths=True,
                )
            ],
        )
        compiler_map["nvhpc"] = compiler_section_for(
            "nvhpc",
            [
                compiler_def(
                    "nvhpc@21.3",
                    "/path/is/now/needed/",  # <-- TODO: this needs to be filled in
                    {"c": "cc", "cxx": "CC", "fortran": "ftn"},
                    modules=["PrgEnv-nvidia", "nvidia/21.3"],
                    compilers_use_relative_paths=True,
                )
            ],
        )

        collected = list()
        compiler_variant = self.spec.variants["compiler"][0]
        for key, cfg in compiler_map.items():
            if key in compiler_variant:
                collected.append(cfg)
        return merge_dicts(*collected)

    def cuda_config(self, cuda_version):
        if cuda_version == "10.2.89":
            return {
                "packages": {
                    "cuda": {
                        "externals": [
                            {
                                "spec": "cuda@10.2.89",
                                "prefix": "/opt/nvidia/cudatoolkit10.2/10.2.89_3.28-2.1__g52c0314",
                            }
                        ]
                    }
                }
            }
        else:
            return {
                "packages": {
                    "cuda": {
                        "externals": [
                            {
                                "spec": "cuda@{self.cuda_version}",
                                "prefix": "/usr/local/cuda-{self.cuda_version.major}",
                            }
                        ]
                    }
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
                    "default-mpi": {"pkg_spec": "cray-mpich@7.7.18"},
                }
            }
        }
