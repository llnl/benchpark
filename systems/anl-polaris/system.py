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
)


class AnlPolaris(System):

    maintainers("homerdin")

    id_to_resources = {
        "polaris": {
            "cpu_arch": "zen3",
            "cuda_arch": "80",
            "sys_cores_per_node": 64,
            "sys_gpus_per_node": 4,
            "system_site": "anl",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-zen3-A100-Slingshot/hardware_description.yaml",
            "queues": [JobQueue("prod", 1440, 496), JobQueue("debug", 60, 2)],
        },
    }

    variant(
        "compiler",
        default="gcc",
        description="Which compiler to use",
    )

    variant(
        "filesystems",
        default="none",
        values=(
            "home",
            "eagle",
            "grand",
        ),
        multi=False,
        description="Which filesystems to use",
    )

    variant(
        "gtl",
        default=False,
        values=(True, False),
        description="Use GTL-enabled MPI",
    )

    variant(
        "queue",
        default="prod",
        values=("none", "prod", "debug"),
        multi=False,
        description="Submit to queue",
    )

    variant(
        "cuda",
        default="12.9",
        values=("12.9", "13.0"),
        description="CUDA version",
    )
    variant(
        "bank",
        default="benchpark-aurora",
        values=("none", "Performance", "Operations", "benchpark-aurora"),
        multi=False,
        description="Submit a job to a specific named bank",
    )


    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [CudaSystem(), OpenMPCPUOnlySystem()]

        self.gcc_version = Version("14.3.0")
        self.ofi_gcc_version = "12.3"
        self.mpi_version = Version("9.1.0")
        self.cuda_version = Version(self.spec.variants["cuda"][0])
        self.gtl_flag = self.spec.variants["gtl"][0]

        self.scheduler = "pbs"
        attrs = self.id_to_resources.get("polaris")
        for k, v in attrs.items():
            setattr(self, k, v)

    def mpi_config(self):
        gtl = self.spec.variants["gtl"][0]

        if self.spec.satisfies("compiler=gcc"):
            if gtl:
                gtl_spec = "+gtl"
            else:
                gtl_spec = "~gtl"

            return {
                "packages": {
                    "cray-mpich": {
                        "externals": [
                            {
                                "spec": f"cray-mpich@{self.mpi_version}{gtl_spec}+wrappers +cuda cuda_arch=80 %gcc@{self.gcc_version}",
                                "prefix": f"/opt/cray/pe/mpich/{self.mpi_version}/ofi/gnu/{self.ofi_gcc_version}",
                                "extra_attributes": {
                                    "environment": {
                                        "append_path": {
                                            "LD_LIBRARY_PATH": f"/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib:/opt/cray/pe/mpich/{self.mpi_version}/ofi/gnu/{self.ofi_gcc_version}/lib"
                                        }
                                    },
                                    "gtl_lib_path": f"/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib",
                                    "ldflags": f"-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/gnu/{self.short_gcc_version}/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -lmpi_gtl_cuda",
                                    "gtl_libs": "libmpi_gtl_cuda",
                                },
                            }
                        ]
                    }
                }
            }

    def compute_compilers_section(self):
        return compiler_section_for(
            "gcc",
            [
                compiler_def(
                    "gcc@14.3.0 languages:=c,c++,fortran",
                    "/opt/cray/pe/gcc-native/14/",
                    {"c": "gcc", "cxx": "g++", "fortran": "gfortran"},
                    modules=["PrgEnv-gnu", "gcc/14.3.0"],
                    compilers_use_relative_paths=True,
                    env={
                        "append_path": {
                            "LD_LIBRARY_PATH": "/opt/cray/libfabric/2.3.1/lib64/:/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/cuda/12.9/lib64"
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
                            "spec": "cray-mpich@9.0.1",
                            "prefix": "/opt/cray/pe/mpich/9.1.0/ofi/gnu/12.3/",
                        }
                    ],
                    "buildable": False,
                },
                "attr": {
                    "externals": [
                        {
                            "spec": "attr@2.4.47%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.4.47"
                    ],
                    "buildable": False
                },
                "bash": {
                    "externals": [
                        {
                            "spec": "bash@4.4%gcc",
                            "prefix": "/"
                        }
                    ],
                    "version": [
                        "4.4"
                    ],
                    "buildable": False
                },
                "binutils": {
                    "externals": [
                        {
                            "spec": "binutils@2.43%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.43"
                    ],
                    "buildable": False
                },
                "automake": {
                    "externals": [
                        {
                            "spec": "automake@1.15.1%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.15.1"
                    ],
                    "buildable": False
                },
                "coreutils": {
                    "externals": [
                        {
                            "spec": "coreutils@8.32%gcc",
                            "prefix": "/"
                        }
                    ],
                    "version": [
                        "8.32"
                    ],
                    "buildable": False
                },
                "bison": {
                    "externals": [
                        {
                            "spec": "bison@3.0.4%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "3.0.4"
                    ],
                    "buildable": False
                },
                "conmon": {
                    "externals": [
                        {
                            "spec": "conmon@2.1.10%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.1.10"
                    ],
                    "buildable": False
                },
                "cpio": {
                    "externals": [
                        {
                            "spec": "cpio@2.13%gcc",
                            "prefix": "/"
                        }
                    ],
                    "version": [
                        "2.13"
                    ],
                    "buildable": False
                },
                "findutils": {
                    "externals": [
                        {
                            "spec": "findutils@4.8.0%gcc",
                            "prefix": "/"
                        }
                    ],
                    "version": [
                        "4.8.0"
                    ],
                    "buildable": False
                },
                "diffutils": {
                    "externals": [
                        {
                            "spec": "diffutils@3.6%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "3.6"
                    ],
                    "buildable": False
                },
                "flex": {
                    "externals": [
                        {
                            "spec": "flex@2.6.4%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.6.4"
                    ],
                    "buildable": False
                },
                "gawk": {
                    "externals": [
                        {
                            "spec": "gawk@4.2.1%gcc",
                            "prefix": "/"
                        }
                    ],
                    "version": [
                        "4.2.1"
                    ],
                    "buildable": False
                },
                "git": {
                    "externals": [
                        {
                            "spec": "git@2.43.0%gcc",
                            "prefix": "/usr/share/doc/packages/git"
                        }
                    ],
                    "version": [
                        "2.43.0"
                    ],
                    "buildable": False
                },
                "gnupg": {
                    "externals": [
                        {
                            "spec": "gnupg@2.4.4%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.4.4"
                    ],
                    "buildable": False
                },
                "glibc": {
                    "externals": [
                        {
                            "spec": "glibc@2.38%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.38"
                    ],
                    "buildable": False
                },
                "grep": {
                    "externals": [
                        {
                            "spec": "grep@3.1%gcc",
                            "prefix": "/"
                        }
                    ],
                    "version": [
                        "3.1"
                    ],
                    "buildable": False
                },
                "kbproto": {
                    "externals": [
                        {
                            "spec": "kbproto@1.0.7%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.0.7"
                    ],
                    "buildable": False
                },
                "groff": {
                    "externals": [
                        {
                            "spec": "groff@1.22.4%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.22.4"
                    ],
                    "buildable": False
                },
                "keyutils": {
                    "externals": [
                        {
                            "spec": "keyutils@1.6.3%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.6.3"
                    ],
                    "buildable": False
                },
                "krb5": {
                    "externals": [
                        {
                            "spec": "krb5@1.20.1%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.20.1"
                    ],
                    "buildable": False
                },
                "libfabric": {
                    "externals": [
                        {
                            "spec": "libfabric@2.3.1%gcc",
                            "prefix": "/opt/cray/libfabric/2.3.1"
                        }
                    ],
                    "version": [
                        "1.22.0"
                    ],
                    "buildable": False
                },
                "libelf": {
                    "externals": [
                        {
                            "spec": "libelf@0.185%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "0.185"
                    ],
                    "buildable": False
                },
                "libiberty": {
                    "externals": [
                        {
                            "spec": "libiberty@2.43%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.43"
                    ],
                    "buildable": False
                },
                "libffi": {
                    "externals": [
                        {
                            "spec": "libffi@3.2.1%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "3.2.1"
                    ],
                    "buildable": False
                },
                "libpthread-stubs": {
                    "externals": [
                        {
                            "spec": "libpthread-stubs@0.4%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "0.4"
                    ],
                    "buildable": False
                },
                "libtool": {
                    "externals": [
                        {
                            "spec": "libtool@2.4.6%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.4.6"
                    ],
                    "buildable": False
                },
                "libuuid": {
                    "externals": [
                        {
                            "spec": "libuuid@2.39.3%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.39.3"
                    ],
                    "buildable": False
                },
                "libverto": {
                    "externals": [
                        {
                            "spec": "libverto@0.2.6%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "0.2.6"
                    ],
                    "buildable": False
                },
                "libxcrypt": {
                    "externals": [
                        {
                            "spec": "libxcrypt@4.4.15%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "4.4.15"
                    ],
                    "buildable": False
                },
                "libxcb": {
                    "externals": [
                        {
                            "spec": "libxcb@1.13%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.13"
                    ],
                    "buildable": False
                },
                "libx11": {
                    "externals": [
                        {
                            "spec": "libx11@1.8.7%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.8.7"
                    ],
                    "buildable": False
                },
                "libyaml": {
                    "externals": [
                        {
                            "spec": "libyaml@0.1.7%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "0.1.7"
                    ],
                    "buildable": False
                },
                "lustre": {
                    "externals": [
                        {
                            "spec": "lustre@2.15.6.1%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.15.6.1"
                    ],
                    "buildable": False
                },
                "m4": {
                    "externals": [
                        {
                            "spec": "m4@1.4.18%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.4.18"
                    ],
                    "buildable": False
                },
                "pciutils": {
                    "externals": [
                        {
                            "spec": "pciutils@3.5.6%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "3.5.6"
                    ],
                    "buildable": False
                },
                "ncurses": {
                    "externals": [
                        {
                            "spec": "ncurses@6.1%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "6.1"
                    ],
                    "buildable": False
                },
                "openssh": {
                    "externals": [
                        {
                            "spec": "openssh@9.6%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "9.6"
                    ],
                    "buildable": False
                },
                "pcre2": {
                    "externals": [
                        {
                            "spec": "pcre2@10.42%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "10.42"
                    ],
                    "buildable": False
                },
                "net-snmp": {
                    "externals": [
                        {
                            "spec": "net-snmp@5.9.4%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "5.9.4"
                    ],
                    "buildable": False
                },
                "pinentry": {
                    "externals": [
                        {
                            "spec": "pinentry@1.1.0%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.1.0"
                    ],
                    "buildable": False
                },
                "pmix": {
                    "externals": [
                        {
                            "spec": "pmix@5.0.3%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "5.0.3"
                    ],
                    "buildable": False
                },
                "pkg-config": {
                    "externals": [
                        {
                            "spec": "pkg-config@0.29.2%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "0.29.2"
                    ],
                    "buildable": False
                },
                "popt": {
                    "externals": [
                        {
                            "spec": "popt@1.16%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.16"
                    ],
                    "buildable": False
                },
                "runc": {
                    "externals": [
                        {
                            "spec": "runc@1.2.6%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.2.6"
                    ],
                    "buildable": False
                },
                "rpm": {
                    "externals": [
                        {
                            "spec": "rpm@4.14.3%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "4.14.3"
                    ],
                    "buildable": False
                },
                "rsync": {
                    "externals": [
                        {
                            "spec": "rsync@3.2.7%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "3.2.7"
                    ],
                    "buildable": False
                },
                "sed": {
                    "externals": [
                        {
                            "spec": "sed@4.9%gcc",
                            "prefix": "/"
                        }
                    ],
                    "version": [
                        "4.9"
                    ],
                    "buildable": False
                },
                "shared-mime-info": {
                    "externals": [
                        {
                            "spec": "shared-mime-info@2.4%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.4"
                    ],
                    "buildable": False
                },
                "shadow": {
                    "externals": [
                        {
                            "spec": "shadow@4.8.1%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "4.8.1"
                    ],
                    "buildable": False
                },
                "tar": {
                    "externals": [
                        {
                            "spec": "tar@1.34%gcc",
                            "prefix": "/"
                        }
                    ],
                    "version": [
                        "1.34"
                    ],
                    "buildable": False
                },
                "tk": {
                    "externals": [
                        {
                            "spec": "tk@8.6.12%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "8.6.12"
                    ],
                    "buildable": False
                },
                "systemd": {
                    "externals": [
                        {
                            "spec": "systemd@254.24%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "254.24"
                    ],
                    "buildable": False
                },
                "tcsh": {
                    "externals": [
                        {
                            "spec": "tcsh@6.20.00%gcc",
                            "prefix": "/"
                        }
                    ],
                    "version": [
                        "6.20.00"
                    ],
                    "buildable": False
                },
                "slirp4netns": {
                    "externals": [
                        {
                            "spec": "slirp4netns@1.2.2%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.2.2"
                    ],
                    "buildable": False
                },
                "which": {
                    "externals": [
                        {
                            "spec": "which@2.21%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.21"
                    ],
                    "buildable": False
                },
                "unzip": {
                    "externals": [
                        {
                            "spec": "unzip@6.00%gcc",
                            "prefix": "/usr/bin"
                        }
                    ],
                    "version": [
                        "6.00"
                    ],
                    "buildable": False
                },
                "util-linux": {
                    "externals": [
                        {
                            "spec": "util-linux@2.39.3%gcc",
                            "prefix": "/"
                        }
                    ],
                    "version": [
                        "2.39.3"
                    ],
                    "buildable": False
                },
                "tcl": {
                    "externals": [
                        {
                            "spec": "tcl@8.6.12%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "8.6.12"
                    ],
                    "buildable": False
                },
                "xproto": {
                    "externals": [
                        {
                            "spec": "xproto@7.0.31%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "7.0.31"
                    ],
                    "buildable": False
                },
                "xmlto": {
                    "externals": [
                        {
                            "spec": "xmlto@0.0.26%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "0.0.26"
                    ],
                    "buildable": False
                },
                "zlib": {
                    "externals": [
                        {
                            "spec": "zlib@1.2.13%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.2.13"
                    ],
                    "buildable": False
                },
                "gcc-runtime": {
                    "externals": [
                        {
                            "spec": "gcc-runtime@7.5.0%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "7.5.0"
                    ]
                },
                "openssl": {
                    "externals": [
                        {
                            "spec": "openssl@3.1.4%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "3.1.4"
                    ],
                    "buildable": False
                },
                "zstd": {
                    "externals": [
                        {
                            "spec": "zstd@1.5.5%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.5.5"
                    ],
                    "buildable": False
                },
                "ruby": {
                    "externals": [
                        {
                            "spec": "ruby@2.5.9%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.5.9"
                    ]
                },
                "check": {
                    "externals": [
                        {
                            "spec": "check@0.15.2%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "0.15.2"
                    ],
                    "buildable": False
                },
                "gdrcopy": {
                    "externals": [
                        {
                            "spec": "gdrcopy@2.4.3%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "2.4.3"
                    ],
                    "buildable": False
                },
                "glproto": {
                    "externals": [
                        {
                            "spec": "glproto@1.4.17%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.4.17"
                    ],
                    "buildable": False
                },
                "libtirpc": {
                    "externals": [
                        {
                            "spec": "libtirpc@1.3.4%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "1.3.4"
                    ],
                    "buildable": False
                },
                "spindle": {
                    "externals": [
                        {
                            "spec": "spindle@0.13%gcc",
                            "prefix": "/usr"
                        }
                    ],
                    "version": [
                        "0.13"
                    ],
                    "buildable": False
                },
                "pkgconf": {
                    "buildable": False
                },
                "zlib-ng": {
                    "buildable": False
                },
                "mpi": {"buildable": False},
            }
        }

        print(self.mpi_config())
        selections["packages"] |= self.mpi_config()["packages"]

        if self.spec.satisfies("compiler=gcc"):
            selections["packages"] |= {
                "cray-libsci": {
                    "externals": [
                        {
                            "spec": "cray-libsci@25.09.0",
                            "prefix": "/opt/cray/pe/libsci/26.03.0/GNU/12.3/x86_64/",
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
                            "prefix": "/opt/cray/pe/libsci/26.03.0/CRAY/20.0/x86_64/",
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

        opts.update(
                {
                    "extra_batch_opts": f"-l filesystems={self.spec.variants["filesystems"][0]}",
                }
            )
        
        return opts

    def cuda_config(self, cuda_version):
        return {
            "packages": {
                "blas": {"require": "cray-libsci"},
                "lapack": {"require": "cray-libsci"},
                "curand": {
                    "externals": [
                        {
                            "spec": f"curand@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/math_libs/{cuda_version}/lib64",
                        }
                    ],
                    "buildable": False,
                },
                "cuda": {
                    "externals": [
                        {
                            "spec": f"cuda@{cuda_version}+allow-unsupported-compilers",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/cuda/{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cub": {
                    "externals": [
                        {
                            "spec": f"cub@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/cuda/{cuda_version}",
                        }
                    ],
                    "buildable": False,
                },
                "cublas": {
                    "externals": [
                        {
                            "spec": f"cublas@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/math_libs/{cuda_version}/lib64",
                        }
                    ],
                    "buildable": False,
                },
                "cusolver": {
                    "externals": [
                        {
                            "spec": f"cusolver@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/math_libs/{cuda_version}/lib64",
                        }
                    ],
                    "buildable": False,
                },
                "cufft": {
                    "externals": [
                        {
                            "spec": f"cufft@{cuda_version}",
                            "prefix": f"/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/math_libs/{cuda_version}/lib64",
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
                    "default-mpi": {"pkg_spec": "cray-mpich@9.0.1"},
                    "compiler-gcc": {"pkg_spec": "gcc@12.3.0"},
                    "mpi-gcc": {"pkg_spec": "cray-mpich+gtl"},
                }
            }
        }
