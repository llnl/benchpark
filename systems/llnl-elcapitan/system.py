# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib
from packaging.version import Version

from benchpark.directives import variant, maintainers
from benchpark.system import System
from benchpark.paths import hardware_descriptions


class LlnlElcapitan(System):

    id_to_resources = {
        "tioga": {
            "rocm_arch": "gfx90a",
            "sys_cores_per_node": 64,
            "sys_gpus_per_node": 8,
            "system_site": "llnl",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-zen3-MI250X-Slingshot/hardware_description.yaml",
        },
        "elcapitan": {
            "rocm_arch": "gfx940",
            "sys_cores_per_node": 128,
            "sys_gpus_per_node": 4,
            "system_site": "llnl",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-zen4-MI300A-Slingshot/hardware_description.yaml",
        },
    }

    variant(
        "cluster",
        default="tioga",
        values=("tioga", "elcapitan"),
        description="Which cluster to run on",
    )

    variant(
        "rocm",
        default="5.5.1",
        values=("5.4.3", "5.5.1", "6.2.4"),
        description="ROCm version",
    )

    variant(
        "compiler",
        default="cce",
        values=("cce", "gcc", "rocmcc"),
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
        default="intel-oneapi-mkl",
        values=("intel-oneapi-mkl", "cray-libsci", "rocsolver"),
        description="Which lapack to use",
    )

    variant(
        "blas",
        default="intel-oneapi-mkl",
        values=("intel-oneapi-mkl", "rocblas"),
        description="Which blas to use",
    )

    def initialize(self):
        super().initialize()

        # TODO: Replace this with lookups into the working set
        self.rocm_version = Version(self.spec.variants["rocm"][0])
        if self.spec.satisfies("compiler=gcc"):
            self.gcc_version = Version("12.2.0")
            self.mpi_version = Version("8.1.26")
        else:
            if self.rocm_version >= Version("6.0.0"):
                self.cce_version = Version("18.0.1")
                self.mpi_version = Version("8.1.31")
            else:
                self.cce_version = Version("16.0.0")
                self.mpi_version = Version("8.1.26")
            self.short_cce_version = (
                f"{self.cce_version.major}.{self.cce_version.minor}"
            )
        if self.rocm_version >= Version("6.0.0"):
            self.pmi_version = Version("6.1.15.6")
            self.llvm_version = Version("18.0.1")
        else:
            self.pmi_version = Version("6.1.12")
            self.llvm_version = Version("16.0.0")
        # TODO: Replace this with lookups into the working set

        self.scheduler = "flux"
        attrs = self.id_to_resources.get(self.spec.variants["cluster"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def generate_description(self, output_dir):
        super().generate_description(output_dir)

        sw_description = pathlib.Path(output_dir) / "software.yaml"

        with open(sw_description, "w") as f:
            f.write(self.sw_description())

    def system_specific_variables(self):
        return {"rocm_arch": self.rocm_arch}

    def external_pkg_configs(self):
        externals = LlnlElcapitan.resource_location / "externals"

        selections = [externals / "base" / "00-packages.yaml"]

        rocm_cfg_path = self.next_adhoc_cfg()
        with open(rocm_cfg_path, "w") as f:
            f.write(self.rocm_config())
        selections.append(rocm_cfg_path)

        mpi_cfg_path = self.next_adhoc_cfg()
        with open(mpi_cfg_path, "w") as f:
            f.write(self.mpi_config())
        selections.append(mpi_cfg_path)

        if self.spec.satisfies("compiler=cce"):
            selections.append(externals / "libsci" / "01-cce-packages.yaml")
        elif self.spec.satisfies("compiler=gcc"):
            selections.append(externals / "libsci" / "00-gcc-packages.yaml")

        cmp_preference_path = self.next_adhoc_cfg()
        with open(cmp_preference_path, "w") as f:
            f.write(self.compiler_weighting_cfg())
        selections.append(cmp_preference_path)

        return selections

    def compiler_weighting_cfg(self):
        compiler = self.spec.variants["compiler"][0]

        if compiler == "cce":
            return """\
packages:
  all:
    require:
    - one_of: ["%cce", "%gcc"]
"""
        elif compiler == "gcc":
            return """\
packages: {}
"""
        elif compiler == "rocmcc":
            return """\
packages: {}
"""
        else:
            raise ValueError(f"Unexpected value for compiler: {compiler}")

    def compiler_configs(self):
        compilers = LlnlElcapitan.resource_location / "compilers"

        selections = []
        if self.spec.satisfies("compiler=cce") or self.spec.satisfies(
            "compiler=rocmcc"
        ):
            compiler_cfg_path = self.next_adhoc_cfg()
            with open(compiler_cfg_path, "w") as f:
                f.write(self.rocm_cce_compiler_cfg())
            selections.append(compiler_cfg_path)

        # Note: this is always included for some low-level dependencies
        # that shouldn't build with %cce
        selections.append(compilers / "gcc" / "00-gcc-12-compilers.yaml")

        return selections

    def mpi_config(self):
        gtl = self.spec.variants["gtl"][0]

        if self.spec.satisfies("compiler=cce"):
            dont_use_gtl = f"""\
        gtl_lib_path: /opt/cray/pe/mpich/{self.mpi_version}/gtl/lib
        ldflags: "-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib"
"""

            use_gtl = f"""\
        gtl_flags: $MV2_COMM_WORLD_LOCAL_RANK
        gtl_cutoff_size: 4096
        fi_cxi_ats: 0
        gtl_lib_path: /opt/cray/pe/mpich/{self.mpi_version}/gtl/lib
        gtl_libs: ["libmpi_gtl_hsa"]
        ldflags: "-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -lmpi_gtl_hsa"
"""

            if gtl:
                gtl_spec = "+gtl"
                gtl_cfg = use_gtl
            else:
                gtl_spec = "~gtl"
                gtl_cfg = dont_use_gtl

            return f"""\
packages:
  cray-mpich:
    externals:
    - spec: cray-mpich@{self.mpi_version}%cce@{self.cce_version} {gtl_spec} +wrappers
      prefix: /opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}
      extra_attributes:
{gtl_cfg}
"""
        elif self.spec.satisfies("compiler=rocmcc"):
            dont_use_gtl = f"""\
        gtl_lib_path: /opt/cray/pe/mpich/{self.mpi_version}/gtl/lib
        ldflags: "-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib"
"""

            use_gtl = f"""\
        gtl_cutoff_size: 4096
        fi_cxi_ats: 0
        gtl_lib_path: /opt/cray/pe/mpich/{self.mpi_version}/gtl/lib
        gtl_libs: ["libmpi_gtl_hsa"]
        ldflags: "-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -lmpi_gtl_hsa"
"""

            if gtl:
                gtl_spec = "+gtl"
                gtl_cfg = use_gtl
            else:
                gtl_spec = "~gtl"
                gtl_cfg = dont_use_gtl

            return f"""\
packages:
  cray-mpich:
    externals:
    - spec: cray-mpich@{self.mpi_version}%cce@{self.cce_version} {gtl_spec} +wrappers
      prefix: /opt/cray/pe/mpich/{self.mpi_version}/ofi/crayclang/{self.short_cce_version}
      extra_attributes:
{gtl_cfg}
"""
        elif self.spec.satisfies("compiler=gcc"):
            return f"""\
packages:
  cray-mpich:
    externals:
    - spec: cray-mpich@{self.mpi_version}%gcc@{self.gcc_version} ~gtl +wrappers
      prefix: /opt/cray/pe/mpich/{self.mpi_version}/ofi/gnu/10.3
      extra_attributes:
        gtl_lib_path: /opt/cray/pe/mpich/{self.mpi_version}/gtl/lib
        ldflags: "-L/opt/cray/pe/mpich/{self.mpi_version}/ofi/gnu/10.3/lib -lmpi -L/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{self.mpi_version}/gtl/lib"
"""

    def rocm_config(self):
        return f"""\
packages:
  blas:
    require:
      - {self.spec.variants["blas"][0]}
  lapack:
    require:
      - {self.spec.variants["lapack"][0]}
  hipfft:
    externals:
    - spec: hipfft@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
  rocfft:
    externals:
    - spec: rocfft@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
  rocprim:
    externals:
    - spec: rocprim@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
  rocrand:
    externals:
    - spec: rocrand@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
  rocsparse:
    externals:
    - spec: rocsparse@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
  rocthrust:
    externals:
    - spec: rocthrust@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
  hip:
    externals:
    - spec: hip@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
  hsa-rocr-dev:
    externals:
    - spec: hsa-rocr-dev@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
  comgr:
    externals:
    - spec: comgr@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}/
    buildable: false
  hiprand:
    externals:
    - spec: hiprand@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
  hipsparse:
    externals:
    - spec: hipsparse@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
  hipblas:
    externals:
    - spec: hipblas@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}/
    buildable: false
  hipsolver:
    externals:
    - spec: hipsolver@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}/
    buildable: false
  hsakmt-roct:
    externals:
    - spec: hsakmt-roct@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}/
    buildable: false
  roctracer-dev-api:
    externals:
    - spec: roctracer-dev-api@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}/
    buildable: false
  rocminfo:
    externals:
    - spec: rocminfo@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}/
    buildable: false
  llvm:
    externals:
    - spec: llvm@{self.llvm_version}
      prefix: /opt/rocm-{self.rocm_version}/llvm
    buildable: false
  llvm-amdgpu:
    externals:
    - spec: llvm-amdgpu@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}/llvm
    buildable: false
  rocblas:
    externals:
    - spec: rocblas@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
  rocsolver:
    externals:
    - spec: rocsolver@{self.rocm_version}
      prefix: /opt/rocm-{self.rocm_version}
    buildable: false
"""

    def rocm_cce_compiler_cfg(self):
        if self.spec.satisfies("compiler=rocmcc"):
            return f"""\
compilers:
- compiler:
    spec: rocmcc@{self.rocm_version}
    paths:
      cc:  /opt/rocm-{self.rocm_version}/bin/amdclang
      cxx:  /opt/rocm-{self.rocm_version}/bin/amdclang++
      f77: /opt/rocm-{self.rocm_version}/bin/amdflang
      fc:  /opt/rocm-{self.rocm_version}/bin/amdflang
    flags:
      cflags: -g -O2
      cxxflags: -g -O2
    operating_system: rhel8
    target: x86_64
    modules:
    - cce/{self.cce_version}
    environment:
      set:
        RFE_811452_DISABLE: '1'
      append_path:
        LD_LIBRARY_PATH: /opt/cray/pe/gcc-libs
      prepend_path:
        LD_LIBRARY_PATH: "/opt/cray/pe/cce/{self.cce_version}/cce/x86_64/lib:/opt/cray/pe/pmi/{self.pmi_version}/lib"
        LIBRARY_PATH: /opt/rocm-{self.rocm_version}/lib
    extra_rpaths:
    - /opt/rocm-{self.rocm_version}/lib
    - /opt/cray/pe/gcc-libs
    - /opt/cray/pe/cce/{self.cce_version}/cce/x86_64/lib
"""
        else:
            return f"""\
compilers:
- compiler:
    spec: cce@{self.cce_version}-rocm{self.rocm_version}
    paths:
      cc:  /opt/cray/pe/cce/{self.cce_version}/bin/craycc
      cxx:  /opt/cray/pe/cce/{self.cce_version}/bin/crayCC
      f77:  /opt/cray/pe/cce/{self.cce_version}/bin/crayftn
      fc:  /opt/cray/pe/cce/{self.cce_version}/bin/crayftn
    flags:
      cflags: -g -O2
      cxxflags: -g -O2 -std=c++14
      fflags: -g -O2 -hnopattern
      ldflags: -ldl
    operating_system: rhel8
    target: x86_64
    modules:
    - cce/{self.cce_version}
    environment:
      prepend_path:
        LD_LIBRARY_PATH: "/opt/cray/pe/cce/{self.cce_version}/cce/x86_64/lib:/opt/rocm-{self.rocm_version}/lib"
    extra_rpaths: [/opt/cray/pe/cce/{self.cce_version}/cce/x86_64/lib/, /opt/cray/pe/gcc-libs/, /opt/rocm-{self.rocm_version}/lib]
"""

    def sw_description(self):
        """This is somewhat vestigial: for the Tioga config that is committed
        to the repo, multiple instances of mpi/compilers are stored and
        and these variables were used to choose consistent dependencies.
        The configs generated by this class should only ever have one
        instance of MPI etc., so there is no need for that. The experiments
        will fail if these variables are not defined though, so for now
        they are still generated (but with more-generic values).
        """
        return f"""\
software:
  packages:
    default-compiler:
      pkg_spec: "{self.spec.variants["compiler"][0]}"
    default-mpi:
      pkg_spec: cray-mpich
    compiler-rocm:
      pkg_spec: cce
    compiler-amdclang:
      pkg_spec: clang
    compiler-gcc:
      pkg_spec: gcc
    mpi-rocm-gtl:
      pkg_spec: cray-mpich+gtl
    mpi-rocm-no-gtl:
      pkg_spec: cray-mpich~gtl
    mpi-gcc:
      pkg_spec: cray-mpich~gtl
    blas:
      pkg_spec: "{self.spec.variants["blas"][0]}"
    blas-rocm:
      pkg_spec: rocblas
    lapack:
      pkg_spec: "{self.spec.variants["lapack"][0]}"
    lapack-oneapi:
      pkg_spec: intel-oneapi-mkl
    lapack-rocm:
      pkg_spec: rocsolver
"""
