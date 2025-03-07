# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from benchpark.directives import variant
from benchpark.system import System
from packaging.version import Version


class OlcfFrontier(System):

    variant(
        "compiler",
        default="cce",
        values=("gcc", "cce", "amd"),
        description="Which compiler to use",
    )
    variant(
        "rocm",
        default="6.2.4",
        description="ROCm version",
    )

    def initialize(self):
        super().initialize()

        self.rocm_version = Version(self.spec.variants["rocm"][0])

        full_versions = {"cce": "18.0.1", "amd": "6.2.4", "gcc": "13"}
        for key, value in full_versions.items():
            if key == self.spec.variants["compiler"][0]:
                self.compiler_version = Version(value)

        sys_variables = {
            "sys_cores_per_node": 56,
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
        externals = OlcfFrontier.resource_location / "externals"

        selections = [externals / "base" / "00-packages.yaml"]
        rocm_cfg_path = self.next_adhoc_cfg()
        with open(rocm_cfg_path, "w") as f:
            f.write(self.rocm_config())
        selections.append(rocm_cfg_path)
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
        cc:  /opt/rocm-{self.rocm_version}/bin/amdclang
        cxx: /opt/rocm-{self.rocm_version}/bin/amdclang++
        f77: /opt/rocm-{self.rocm_version}/bin/amdflang
        fc:  /opt/rocm-{self.rocm_version}/bin/amdflang
      operating_system: sles15
      target: any
      environment:
        set:
          RFE_811452_DISABLE: '1'
          GCC_X86_64: /usr
      extra_rpaths:
      - /opt/rocm-{self.rocm_version}/lib
      modules:
      - PrgEnv-amd/8.6.0
      - craype/2.7.33
      - cray-dsmml/0.3.0
      - cray-mpich/8.1.31
      - cray-libsci/24.11.0
      - amd/6.2.4
      - craype-x86-trento
      - cray-pmi/6.1.15
      - libfabric
      - xpmem
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
      operating_system: sles15
      target: any
      modules: []
      environment:
        set:
          RFE_811452_DISABLE: '1'
          GCC_X86_64: /usr
          CRAYLIBS_X86_64: /opt/cray/pe/cce/{self.compiler_version}/cce/x86_64/lib
        prepend_path:
          LD_LIBRARY_PATH: /usr/lib64/gcc/x86_64-suse-linux/13
      extra_rpaths:
      - /usr/lib64/gcc/x86_64-suse-linux/13
      modules:
      - PrgEnv-cray/8.6.0
      - craype/2.7.33
      - cray-dsmml/0.3.0
      - cray-mpich/8.1.31
      - cray-libsci/24.11.0
      - cce/18.0.1
      - craype-x86-trento
      - cray-pmi/6.1.15
      - libfabric
      - xpmem
"""

    def gcc_compiler_cfg(self):
        return f"""\
compilers:
  - compiler:
      spec: gcc@{self.compiler_version}
      paths:
        cc: /usr/bin/gcc-{self.compiler_version}
        cxx: /usr/bin/g++-{self.compiler_version}
        f77: /usr/bin/gfortran-{self.compiler_version}
        fc: /usr/bin/gfortran-{self.compiler_version}
      operating_system: sles15
      target: any
      extra_rpaths: []
      modules:
      - PrgEnv-gnu/8.6.0
      - craype/2.7.33
      - cray-dsmml/0.3.0
      - cray-mpich/8.1.31
      - cray-libsci/24.11.0
      - gcc-native/13.2
      - craype-x86-trento
      - cray-pmi/6.1.15
      - libfabric
      - xpmem
"""

    def rocm_config(self):
        return f"""\
packages:
  comgr:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: comgr@{self.rocm_version}
  hip:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: hip@{self.rocm_version}
      modules:
      - rocm/{self.rocm_version}
  hip-rocclr:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: hip-rocclr@{self.rocm_version}
  hipblas:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: hipblas@{self.rocm_version}
  hipcub:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: hipcub@{self.rocm_version}
  hipfft:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: hipfft@{self.rocm_version}
  hipify-clang:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: hipify-clang@{self.rocm_version}
  hipsparse:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: hipsparse@{self.rocm_version}
  hsa-rocr-dev:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: hsa-rocr-dev@{self.rocm_version}
  hsakmt-roct:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: hsakmt-roct@{self.rocm_version}
  llvm-amdgpu:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}/lib/llvm
      spec: llvm-amdgpu@{self.rocm_version}
  rccl:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rccl@{self.rocm_version}
  rocalution:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocalution@{self.rocm_version}
  rocblas:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocblas@{self.rocm_version}
  rocfft:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocfft@{self.rocm_version}
    variants: amdgpu_target=gfx90a amdgpu_target_sram_ecc=gfx90a
  rocm-clang-ocl:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocm-clang-ocl@{self.rocm_version}
  rocm-cmake:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocm-cmake@{self.rocm_version}
  rocm-device-libs:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocm-device-libs@{self.rocm_version}
  rocm-gdb:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocm-gdb@{self.rocm_version}
  rocm-opencl:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}/opencl
      spec: rocm-opencl@{self.rocm_version}
  rocm-opencl-runtime:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}/opencl
      spec: rocm-opencl-runtime@{self.rocm_version}
  rocm-openmp-extras:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}/llvm
      spec: rocm-openmp-extras@{self.rocm_version}
  rocm-smi:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}/rocm_smi
      spec: rocmsmi@{self.rocm_version}
  rocm-smi-lib:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}/rocm_smi
      spec: rocm-smi-lib@{self.rocm_version}
  rocminfo:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocminfo@{self.rocm_version}
  rocprim:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocprim@{self.rocm_version}
  rocprofiler-dev:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocprofiler-dev@{self.rocm_version}
  rocrand:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocrand@{self.rocm_version}
  rocsolver:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocsolver@{self.rocm_version}
  rocsparse:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocsparse@{self.rocm_version}
  rocthrust:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
      spec: rocthrust@{self.rocm_version}
  roctracer-dev:
    buildable: false
    externals:
    - prefix: /opt/rocm-{self.rocm_version}
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
