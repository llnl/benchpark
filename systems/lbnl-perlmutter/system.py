# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from packaging.version import Version

from benchpark.directives import variant, maintainers
from benchpark.system import System
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
        },
    }

    variant(
        "compiler",
        default="cce",
        values=("cce", "gcc"),
        description="Which compiler to use",
    )

    def __init__(self, spec):
        super().__init__(spec)

        if self.spec.satisfies("compiler=gcc"):
            self.gcc_version = Version("12.2.0")
            self.mpi_version = Version("8.1.26")

        self.scheduler = "slurm"
        attrs = self.id_to_resources.get("perlmutter")
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute_packages_section(self):
        selections = {
            "packages": {
                "all": {"require": "target=x86_64:"},
                "tar": {"externals": [{"spec": "tar@1.30", "prefix": "/usr"}]},
                "coreutils": {
                    "externals": [{"spec": "coreutils@8.30", "prefix": "/usr"}]
                },
                "libtool": {"externals": [{"spec": "libtool@2.4.6", "prefix": "/usr"}]},
                "flex": {"externals": [{"spec": "flex@2.6.1+lex", "prefix": "/usr"}]},
                "openssl": {
                    "externals": [{"spec": "openssl@1.1.1k", "prefix": "/usr"}]
                },
                "m4": {"externals": [{"spec": "m4@1.4.18", "prefix": "/usr"}]},
                "groff": {"externals": [{"spec": "groff@1.22.3", "prefix": "/usr"}]},
                "cmake": {
                    "externals": [
                        {"spec": "cmake@3.20.2", "prefix": "/usr"},
                        {"spec": "cmake@3.23.1", "prefix": "/usr/tce"},
                        {"spec": "cmake@3.24.2", "prefix": "/usr/tce"},
                    ],
                    "buildable": False,
                },
                "elfutils": {
                    "externals": [{"spec": "elfutils@0.190", "prefix": "/usr"}],
                    "buildable": False,
                },
                "papi": {
                    "externals": [{"spec": "papi@5.6.0.0", "prefix": "/usr"}],
                    "buildable": False,
                },
                "unwind": {
                    "externals": [{"spec": "unwind@8.0.1", "prefix": "/usr"}],
                    "buildable": False,
                },
                "pkgconf": {"externals": [{"spec": "pkgconf@1.4.2", "prefix": "/usr"}]},
                "curl": {
                    "externals": [
                        {"spec": "curl@7.61.1+gssapi+ldap+nghttp2", "prefix": "/usr"}
                    ]
                },
                "gmake": {"externals": [{"spec": "gmake@4.2.1", "prefix": "/usr"}]},
                "subversion": {
                    "externals": [{"spec": "subversion@1.10.2", "prefix": "/usr"}]
                },
                "diffutils": {
                    "externals": [{"spec": "diffutils@3.6", "prefix": "/usr"}]
                },
                "swig": {"externals": [{"spec": "swig@3.0.12", "prefix": "/usr"}]},
                "gawk": {"externals": [{"spec": "gawk@4.2.1", "prefix": "/usr"}]},
                "binutils": {
                    "externals": [{"spec": "binutils@2.30.113", "prefix": "/usr"}]
                },
                "findutils": {
                    "externals": [{"spec": "findutils@4.6.0", "prefix": "/usr"}]
                },
                "git-lfs": {
                    "externals": [{"spec": "git-lfs@2.11.0", "prefix": "/usr/tce"}]
                },
                "ccache": {"externals": [{"spec": "ccache@3.7.7", "prefix": "/usr"}]},
                "automake": {
                    "externals": [{"spec": "automake@1.16.1", "prefix": "/usr"}]
                },
                "cvs": {"externals": [{"spec": "cvs@1.11.23", "prefix": "/usr"}]},
                "git": {
                    "externals": [
                        {"spec": "git@2.31.1+tcltk", "prefix": "/usr"},
                        {"spec": "git@2.29.1+tcltk", "prefix": "/usr/tce"},
                    ]
                },
                "openssh": {"externals": [{"spec": "openssh@8.0p1", "prefix": "/usr"}]},
                "autoconf": {
                    "externals": [{"spec": "autoconf@2.69", "prefix": "/usr"}]
                },
                "texinfo": {"externals": [{"spec": "texinfo@6.5", "prefix": "/usr"}]},
                "bison": {"externals": [{"spec": "bison@3.0.4", "prefix": "/usr"}]},
                "python": {
                    "externals": [
                        {
                            "spec": "python@3.9.12",
                            "prefix": "/usr/tce/packages/python/python-3.9.12",
                            "buildable": False,
                        }
                    ]
                },
                "unzip": {
                    "buildable": False,
                    "externals": [{"spec": "unzip@6.0", "prefix": "/usr"}],
                },
                "hypre": {"variants": "amdgpu_target=gfx90a"},
                "hwloc": {
                    "externals": [
                        {"spec": "hwloc@2.9.1", "prefix": "/usr", "buildable": False}
                    ]
                },
                "fftw": {"buildable": False},
                "intel-oneapi-mkl": {
                    "externals": [
                        {
                            "spec": "intel-oneapi-mkl@2023.2.0",
                            "prefix": "/opt/intel/oneapi",
                        }
                    ],
                    "buildable": False,
                },
                "mpi": {"buildable": False},
                "libfabric": {
                    "externals": [
                        {"spec": "libfabric@2.1", "prefix": "/opt/cray/libfabric/2.1"}
                    ],
                    "buildable": False,
                },
            }
        }

        selections["packages"] |= self.mpi_config()["packages"]

        if self.spec.satisfies("compiler=cce"):
            selections["packages"] |= {
                "cray-libsci": {
                    "externals": [
                        {
                            "spec": "cray-libsci@23.05.1.4%cce",
                            "prefix": "/opt/cray/pe/libsci/23.05.1.4/cray/12.0/x86_64/",
                        }
                    ]
                }
            }
        elif self.spec.satisfies("compiler=gcc"):
            selections["packages"] |= {
                "cray-libsci": {
                    "externals": [
                        {
                            "spec": "cray-libsci@23.05.1.4%gcc",
                            "prefix": "/opt/cray/pe/libsci/23.05.1.4/gnu/10.3/x86_64/",
                        }
                    ]
                }
            }

        selections["packages"] |= self.compiler_weighting_cfg()["packages"]

        return selections

    def compiler_weighting_cfg(self):
        compiler = self.spec.variants["compiler"][0]

        if compiler == "cce":
            return {"packages": {"all": {"require": [{"one_of": ["%cce", "%gcc"]}]}}}
        elif compiler == "gcc":
            return {"packages": {}}
        else:
            raise ValueError(f"Unexpected value for compiler: {compiler}")

    def compute_compilers_section(self):
        selections = {
            "compilers": [
                {
                    "compiler": {
                        "spec": "gcc@12.2.0",
                        "paths": {
                            "cc": "/opt/cray/pe/gcc/12.2.0/bin/gcc",
                            "cxx": "/opt/cray/pe/gcc/12.2.0/bin/g++",
                            "f77": "/opt/cray/pe/gcc/12.2.0/bin/gfortran",
                            "fc": "/opt/cray/pe/gcc/12.2.0/bin/gfortran",
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

        return selections

    def mpi_config(self):
        gtl = self.spec.variants["gtl"][0]

        if self.spec.satisfies("compiler=cce"):
            dont_use_gtl = {
                "gtl_lib_path": f"/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
                "ldflags": f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
            }

            use_gtl = {
                "gtl_flags": "$MV2_COMM_WORLD_LOCAL_RANK",
                "gtl_cutoff_size": 4096,
                "fi_cxi_ats": 0,
                "gtl_lib_path": f"/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
                "gtl_libs": ["libmpi_gtl_hsa"],
                "ldflags": f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -lmpi_gtl_hsa",
            }

            if gtl:
                gtl_spec = "+gtl"
                gtl_cfg = use_gtl
            else:
                gtl_spec = "~gtl"
                gtl_cfg = dont_use_gtl

            return {
                "packages": {
                    "cray-mpich": {
                        "externals": [
                            {
                                "spec": f"cray-mpich@{self.mpi_version}%cce@{self.cce_version} {gtl_spec} +wrappers",
                                "prefix": f"/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}",
                                "extra_attributes": gtl_cfg,  # Assuming `gtl_cfg` is already defined elsewhere
                            }
                        ]
                    }
                }
            }

        elif self.spec.satisfies("compiler=gcc"):
            return {
                "packages": {
                    "cray-mpich": {
                        "externals": [
                            {
                                "spec": f"cray-mpich@{self.mpi_version}%gcc@{self.gcc_version} ~gtl +wrappers",
                                "prefix": f"/opt/cray/pe/mpich/{self.mpi_version}/ofi/gnu/10.3",
                                "extra_attributes": {
                                    "gtl_lib_path": f"/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
                                    "ldflags": f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/gnu/10.3/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
                                },
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
                    "default-mpi": {"pkg_spec": "cray-mpich"},
                    "compiler-amdclang": {"pkg_spec": "clang"},
                    "compiler-gcc": {"pkg_spec": "gcc"},
                    "mpi-gcc": {"pkg_spec": "cray-mpich~gtl"},
                    "blas": {"pkg_spec": f"{self.spec.variants['blas'][0]}"},
                    "lapack": {"pkg_spec": f"{self.spec.variants['lapack'][0]}"},
                    "lapack-oneapi": {"pkg_spec": "intel-oneapi-mkl"},
                }
            }
        }
