# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from benchpark.directives import variant
from benchpark.system import System

id_to_resources = {
    "tioga": {
        "rocm_arch": "gfx90a",
        "sys_cores_per_node": 64,
        "sys_gpus_per_node": 8,
    },
    "elcapitan": {
        "rocm_arch": "gfx940",
        "sys_cores_per_node": 128,
        "sys_gpus_per_node": 4,
    },
}


class LlnlElcapitan(System):

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
        values=("cce", "gcc"),
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

        self.scheduler = "flux"
        attrs = id_to_resources.get(self.spec.variants["cluster"][0])
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
            f.write(self.rocm_config(self.spec.variants["rocm"][0]))
        selections.append(rocm_cfg_path)

        mpi_cfg_path = self.next_adhoc_cfg()
        with open(mpi_cfg_path, "w") as f:
            f.write(self.mpi_config("16.0.0"))
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
        else:
            raise ValueError(f"Unexpected value for compiler: {compiler}")

    def compiler_configs(self):
        compilers = LlnlElcapitan.resource_location / "compilers"

        selections = []
        if self.spec.satisfies("compiler=cce"):
            compiler_cfg_path = self.next_adhoc_cfg()
            with open(compiler_cfg_path, "w") as f:
                f.write(
                    self.rocm_cce_compiler_cfg(self.spec.variants["rocm"][0], "16.0.0")
                )
            selections.append(compiler_cfg_path)

        # Note: this is always included for some low-level dependencies
        # that shouldn't build with %cce
        selections.append(compilers / "gcc" / "00-gcc-12-compilers.yaml")

        return selections

    def mpi_config(self, cce_version):
        gtl = self.spec.variants["gtl"][0]

        short_cce_version = ".".join(cce_version.split(".")[:2])
        mpi_version = "8.1.26"

        if self.spec.satisfies("compiler=cce"):
            dont_use_gtl = f"""\
        gtl_lib_path: /opt/cray/pe/mpich/{mpi_version}/gtl/lib
        ldflags: "-L/opt/cray/pe/mpich/{mpi_version}/ofi/crayclang/{short_cce_version}/lib -lmpi -L/opt/cray/pe/mpich/{mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{mpi_version}/gtl/lib"
"""

            use_gtl = f"""\
        gtl_cutoff_size: 4096
        fi_cxi_ats: 0
        gtl_lib_path: /opt/cray/pe/mpich/{mpi_version}/gtl/lib
        gtl_libs: ["libmpi_gtl_hsa"]
        ldflags: "-L/opt/cray/pe/mpich/{mpi_version}/ofi/crayclang/{short_cce_version}/lib -lmpi -L/opt/cray/pe/mpich/{mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{mpi_version}/gtl/lib -lmpi_gtl_hsa"
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
    - spec: cray-mpich@{mpi_version}%cce@{cce_version} {gtl_spec} +wrappers
      prefix: /opt/cray/pe/mpich/{mpi_version}/ofi/crayclang/{short_cce_version}
      extra_attributes:
{gtl_cfg}
"""
        elif self.spec.satisfies("compiler=gcc"):
            return """\
packages:
  cray-mpich:
    externals:
    - spec: cray-mpich@8.1.26%gcc@12.2.0 ~gtl +wrappers
      prefix: /opt/cray/pe/mpich/8.1.26/ofi/gnu/10.3
      extra_attributes:
        gtl_lib_path: /opt/cray/pe/mpich/8.1.26/gtl/lib
        ldflags: "-L/opt/cray/pe/mpich/8.1.26/ofi/gnu/10.3/lib -lmpi -L/opt/cray/pe/mpich/8.1.26/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/8.1.26/gtl/lib"
"""

    def rocm_config(self, rocm_version):
        template = """\
packages:
  blas:
    require:
      - {blas}
  lapack:
    require:
      - {lapack}
  hipfft:
    externals:
    - spec: hipfft@{x}
      prefix: /opt/rocm-{x}
    buildable: false
  rocfft:
    externals:
    - spec: rocfft@{x}
      prefix: /opt/rocm-{x}
    buildable: false
  rocprim:
    externals:
    - spec: rocprim@{x}
      prefix: /opt/rocm-{x}
    buildable: false
  rocrand:
    externals:
    - spec: rocrand@{x}
      prefix: /opt/rocm-{x}
    buildable: false
  rocsparse:
    externals:
    - spec: rocsparse@{x}
      prefix: /opt/rocm-{x}
    buildable: false
  rocthrust:
    externals:
    - spec: rocthrust@{x}
      prefix: /opt/rocm-{x}
    buildable: false
  hip:
    externals:
    - spec: hip@{x}
      prefix: /opt/rocm-{x}
    buildable: false
  hsa-rocr-dev:
    externals:
    - spec: hsa-rocr-dev@{x}
      prefix: /opt/rocm-{x}
    buildable: false
  comgr:
    externals:
    - spec: comgr@{x}
      prefix: /opt/rocm-{x}/
    buildable: false
  hiprand:
    externals:
    - spec: hiprand@{x}
      prefix: /opt/rocm-{x}
    buildable: false
  hipsparse:
    externals:
    - spec: hipsparse@{x}
      prefix: /opt/rocm-{x}
    buildable: false
  hipblas:
    externals:
    - spec: hipblas@{x}
      prefix: /opt/rocm-{x}/
    buildable: false
  hipsolver:
    externals:
    - spec: hipsolver@{x}
      prefix: /opt/rocm-{x}/
    buildable: false
  hsakmt-roct:
    externals:
    - spec: hsakmt-roct@{x}
      prefix: /opt/rocm-{x}/
    buildable: false
  roctracer-dev-api:
    externals:
    - spec: roctracer-dev-api@{x}
      prefix: /opt/rocm-{x}/
    buildable: false
  rocminfo:
    externals:
    - spec: rocminfo@{x}
      prefix: /opt/rocm-{x}/
    buildable: false
  llvm:
    externals:
    - spec: llvm@16.0.0
      prefix: /opt/rocm-{x}/llvm
    buildable: false
  llvm-amdgpu:
    externals:
    - spec: llvm-amdgpu@{x}
      prefix: /opt/rocm-{x}/llvm
    buildable: false
  rocblas:
    externals:
    - spec: rocblas@{x}
      prefix: /opt/rocm-{x}
    buildable: false
  rocsolver:
    externals:
    - spec: rocsolver@{x}
      prefix: /opt/rocm-{x}
    buildable: false
"""
        return template.format(
            x=rocm_version,
            blas=self.spec.variants["blas"][0],
            lapack=self.spec.variants["lapack"][0],
        )

    def rocm_cce_compiler_cfg(self, rocm_version, cce_version):
        template = """\
compilers:
- compiler:
    spec: cce@{y}-rocm{x}
    paths:
      cc:  /opt/cray/pe/cce/{y}/bin/craycc
      cxx:  /opt/cray/pe/cce/{y}/bin/crayCC
      f77:  /opt/cray/pe/cce/{y}/bin/crayftn
      fc:  /opt/cray/pe/cce/{y}/bin/crayftn
    flags:
      cflags: -g -O2
      cxxflags: -g -O2 -std=c++14
      fflags: -g -O2 -hnopattern
      ldflags: -ldl
    operating_system: rhel8
    target: x86_64
    modules: []
    environment:
      prepend_path:
        LD_LIBRARY_PATH: "/opt/cray/pe/cce/{y}/cce/x86_64/lib:/opt/rocm-{x}/lib"
    extra_rpaths: [/opt/cray/pe/cce/{y}/cce/x86_64/lib/, /opt/cray/pe/gcc-libs/, /opt/rocm-{x}/lib]
- compiler:
    spec: rocmcc@{x}
    paths:
      cc:  /opt/rocm-{x}/bin/amdclang
      cxx:  /opt/rocm-{x}/bin/amdclang++
      f77: /opt/rocm-{x}/bin/amdflang
      fc:  /opt/rocm-{x}/bin/amdflang
    flags:
      cflags: -g -O2
      cxxflags: -g -O2
    operating_system: rhel8
    target: x86_64
    modules: []
    environment:
      set:
        RFE_811452_DISABLE: '1'
      append_path:
        LD_LIBRARY_PATH: /opt/cray/pe/gcc-libs
      prepend_path:
        LD_LIBRARY_PATH: "/opt/cray/pe/cce/{y}/cce/x86_64/lib:/opt/cray/pe/pmi/6.1.12/lib"
        LIBRARY_PATH: /opt/rocm-{x}/lib
    extra_rpaths:
    - /opt/rocm-{x}/lib
    - /opt/cray/pe/gcc-libs
    - /opt/cray/pe/cce/{y}/cce/x86_64/lib
"""
        return template.format(x=rocm_version, y=cce_version)

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
