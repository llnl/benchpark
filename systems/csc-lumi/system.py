# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from benchpark.directives import variant
from benchpark.system import System
from packaging.version import Version

class CscLumi(System):

    variant(
        "compiler",
        default="cce15",
        values=("gcc11", "gcc12", "cce14", "cce15", "cce16"),
        description="Which compiler to use",
    )
    variant(
        "rocm",
        default="5.6.1",
        description="ROCm version",
    )

    def initialize(self):
        super().initialize()


        self.rocm_version = Version(self.spec.variants["rocm"][0])

        full_versions = {
            "cce16": "16.0.1",
            "cce15": "15.0.1",
            "cce14": "14.0.2",
            "gcc12": "12.2.0",
            "gcc11": "11.2.0",
        }
        for key,value in full_versions.items():
            if key == self.spec.variants["compiler"][0]:
                self.compiler_version = Version(value)

        sys_variables = {
            "sys_cores_per_node": 64,
            "sys_gpus_per_node": 8,
            "sys_mem_per_node": 512,
        }

        self.scheduler = "slurm"
        for k, v in sys_variables.items():
            setattr(self, k, v)

    def generate_description(self, output_dir):
        super().generate_description(output_dir)

        sw_description = pathlib.Path(output_dir) / "software.yaml"

        with open(sw_description, "w") as f:
            f.write(self.sw_description())

    def system_specific_variables(self):
        return {
            "rocm_arch": "'gfx90a'",
            "gtl_flag": "''",
        }

    def external_pkg_configs(self):
        externals = CscLumi.resource_location / "externals"

        selections = [externals / "base" / "00-packages.yaml"]
        rocm_cfg_path = self.next_adhoc_cfg()
        with open(rocm_cfg_path, "w") as f:
            f.write(self.rocm_config())
        selections.append(rocm_cfg_path)
        if self.spec.satisfies("compiler=cce"):
            selections.append(externals / "libsci" / "01-cce-packages.yaml")
        elif self.spec.satisfies("compiler=gcc"):
            selections.append(externals / "libsci" / "00-gcc-packages.yaml")
        return selections

    def compiler_configs(self):
        selections = []
        if "cce" in self.spec.variants["compiler"][0]:
            compiler_cfg_path = self.next_adhoc_cfg()
            with open(compiler_cfg_path, "w") as f:
                f.write(self.cce_compiler_cfg())
            selections.append(compiler_cfg_path)
        else:
            compiler_cfg_path = self.next_adhoc_cfg()
            with open(compiler_cfg_path, "w") as f:
                f.write(self.gcc_compiler_cfg())
            selections.append(compiler_cfg_path)
        compiler_cfg_path = self.next_adhoc_cfg()
        with open(compiler_cfg_path, "w") as f:
            f.write(self.rocmcc_cfg())
        selections.append(compiler_cfg_path)

        return selections

    def rocmcc_cfg(self):
        return f"""\
compilers:
  - compiler:
        spec: rocmcc@{self.rocm_version}
        paths:
          cc:  /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/bin/amdclang
          cxx: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/bin/amdclang++
          f77: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/bin/amdflang
          fc:  /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/bin/amdflang
        #flags: " "
        operating_system: sles15
        target: any
        modules: []
        environment:
          set:
            RFE_811452_DISABLE: '1'
          append_path:
            LD_LIBRARY_PATH: /opt/cray/pe/gcc-libs
          prepend_path:
            LD_LIBRARY_PATH: /opt/cray/pe/pmi/6.1.12/lib
            LIBRARY_PATH:  /appl/lumi/SW/CrayEnv/EB/rocm/5.6.1/lib:/appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/lib64
        extra_rpaths:
        - /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/lib
        - /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/lib64
        - /opt/cray/pe/gcc-libs
"""

    def cce_compiler_cfg(self):
        return f"""\
compilers:
  - compiler:
      spec: cce@{self.compiler_version}
      paths:
        cc: /opt/cray/pe/cce/{self.compiler_version}/bin/craycc
        cxx: /opt/cray/pe/cce/{self.compiler_version}/bin/crayCC
        f77: /opt/cray/pe/cce/{self.compiler_version}/bin/crayftn
        fc: /opt/cray/pe/cce/{self.compiler_version}/bin/crayftn
      #flags:
      operating_system: sles15
      target: any
      modules: []
      environment:
        set:
          RFE_811452_DISABLE: '1'
        prepend_path:
          LD_LIBRARY_PATH: /opt/cray/pe/pmi/6.1.12/lib
        append_path:
          LD_LIBRARY_PATH: /opt/cray/pe/gcc-libs
          PKG_CONFIG_PATH: /usr/lib64/pkgconfig
      extra_rpaths:
      - /opt/cray/pe/gcc-libs
"""

    def gcc_compiler_cfg(self):
        return f"""\
compilers:
  - compiler:
      spec: gcc@{self.compiler_version}
      paths:
        cc: /opt/cray/pe/gcc/{self.compiler_version}/bin/gcc
        cxx: /opt/cray/pe/gcc/{self.compiler_version}/bin/g++
        f77: /opt/cray/pe/gcc/{self.compiler_version}/bin/gfortran
        fc: /opt/cray/pe/gcc/{self.compiler_version}/bin/gfortran
      #flags:
      operating_system: sles15
      target: any
      modules: []
      environment:
        prepend_path:
          LD_LIBRARY_PATH: /opt/cray/pe/pmi/6.1.12/lib:/opt/cray/libfabric/1.15.2.0/lib64
          PKG_CONFIG_PATH: /usr/lib64/pkgconfig
      extra_rpaths: []
"""

    def rocm_config(self):
        return f"""\
packages:
  comgr:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: comgr@{self.rocm_version}
  hip:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/hip
      spec: hip@{self.rocm_version}
  hip-rocclr:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/rocclr
      spec: hip-rocclr@{self.rocm_version}
  hipblas:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: hipblas@{self.rocm_version}
  hipcub:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: hipcub@{self.rocm_version}
  hipfft:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: hipfft@{self.rocm_version}
  hipfort:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: hipfort@{self.rocm_version}
  hipify-clang:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: hipify-clang@{self.rocm_version}
  hipsparse:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: hipsparse@{self.rocm_version}
  hsa-rocr-dev:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: hsa-rocr-dev@{self.rocm_version}
  hsakmt-roct:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: hsakmt-roct@{self.rocm_version}
  llvm-amdgpu:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/llvm
      spec: llvm-amdgpu@{self.rocm_version}
  rccl:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rccl@{self.rocm_version}
  rocalution:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocalution@{self.rocm_version}
  rocblas:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocblas@{self.rocm_version}
  rocfft:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocfft@{self.rocm_version}
    variants: amdgpu_target=auto amdgpu_target_sram_ecc=auto
  rocm-clang-ocl:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocm-clang-ocl@{self.rocm_version}
  rocm-cmake:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocm-cmake@{self.rocm_version}
  rocm-device-libs:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocm-device-libs@{self.rocm_version}
  rocm-gdb:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocm-gdb@{self.rocm_version}
  rocm-opencl:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/opencl
      spec: rocm-opencl@{self.rocm_version}
  rocm-opencl-runtime:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/opencl
      spec: rocm-opencl-runtime@{self.rocm_version}
  rocm-openmp-extras:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/llvm
      spec: rocm-openmp-extras@{self.rocm_version}
  rocm-smi:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/rocm_smi
      spec: rocmsmi@{self.rocm_version}
  rocm-smi-lib:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}/rocm_smi
      spec: rocm-smi-lib@{self.rocm_version}
  rocminfo:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocminfo@{self.rocm_version}
  rocprim:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocprim@{self.rocm_version}
  rocprofiler-dev:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocprofiler-dev@{self.rocm_version}
  rocrand:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocrand@{self.rocm_version}
  rocsolver:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocsolver@{self.rocm_version}
  rocsparse:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocsparse@{self.rocm_version}
  rocthrust:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: rocthrust@{self.rocm_version}
  roctracer-dev:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{self.rocm_version}
      spec: roctracer-dev@{self.rocm_version}
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
      pkg_spec: cray-mpich@8.1%cce ~gtl
    compiler-rocm:
      pkg_spec: "{self.spec.variants["compiler"][0]}"
    blas-rocm:
      pkg_spec: rocblas@{self.rocm_version}
    blas:
      pkg_spec: cray-libsci@23
    lapack:
      pkg_spec: cray-libsci@23
    mpi-rocm-gtl:
      pkg_spec: cray-mpich@8.1%cce +gtl
    mpi-rocm-no-gtl:
      pkg_spec: cray-mpich@8.1%cce ~gtl
    mpi-gcc:
      pkg_spec: cray-mpich@8.1%gcc ~gtl
"""
