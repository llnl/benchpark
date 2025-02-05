# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from benchpark.directives import variant
from benchpark.system import System


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

        sys_variables= {
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
            f.write(self.rocm_config(self.spec.variants["rocm"][0]))
        selections.append(rocm_cfg_path)
        if self.spec.satisfies("compiler=cce"):
            selections.append(externals / "libsci" / "01-cce-packages.yaml")
        elif self.spec.satisfies("compiler=gcc"):
            selections.append(externals / "libsci" / "00-gcc-packages.yaml")

        return selections

    def compiler_configs(self):
        compilers = CscLumi.resource_location / "compilers"
        full_versions = {
            "cce16": "16.0.1",
            "cce15": "15.0.1",
            "cce14": "14.0.2",
            "gcc12": "12.2.0",
            "gcc11": "11.2.0",
        }
        selections = []
        if "cce" in self.spec.variants["compiler"][0]:
            compiler_cfg_path = self.next_adhoc_cfg()
            with open(compiler_cfg_path, "w") as f:
                f.write(
                    self.cce_compiler_cfg(
                        full_versions.get(self.spec.variants["compiler"][0])
                    )
                )
            selections.append(compiler_cfg_path)
        else:
            compiler_cfg_path = self.next_adhoc_cfg()
            with open(compiler_cfg_path, "w") as f:
                f.write(self.gcc_compiler_cfg("12.2.0"))
            selections.append(compiler_cfg_path)
        selections.append(
            CscLumi.resource_location / "compilers" / "00-extra-compilers.yaml"
        )
        compiler_cfg_path = self.next_adhoc_cfg()
        with open(compiler_cfg_path, "w") as f:
            f.write(self.rocmcc_cfg(self.spec.variants["rocm"][0]))
        selections.append(compiler_cfg_path)

        return selections

    def rocmcc_cfg(self, rocm_version):
        template = """\
compilers:
  - compiler:
        spec: rocmcc@{x}
        paths:
          cc:  /appl/lumi/SW/CrayEnv/EB/rocm/{x}/bin/amdclang
          cxx: /appl/lumi/SW/CrayEnv/EB/rocm/{x}/bin/amdclang++
          f77: /appl/lumi/SW/CrayEnv/EB/rocm/{x}/bin/amdflang
          fc:  /appl/lumi/SW/CrayEnv/EB/rocm/{x}/bin/amdflang
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
            LIBRARY_PATH:  /appl/lumi/SW/CrayEnv/EB/rocm/5.6.1/lib:/appl/lumi/SW/CrayEnv/EB/rocm/{x}/lib64
        extra_rpaths:
        - /appl/lumi/SW/CrayEnv/EB/rocm/{x}/lib
        - /appl/lumi/SW/CrayEnv/EB/rocm/{x}/lib64
        - /opt/cray/pe/gcc-libs
"""
        return template.format(x=rocm_version)

    def cce_compiler_cfg(self, cce_version):
        template = """\
compilers:
  - compiler:
      spec: cce@{x}
      paths:
        cc: /opt/cray/pe/cce/{x}/bin/craycc
        cxx: /opt/cray/pe/cce/{x}/bin/crayCC
        f77: /opt/cray/pe/cce/{x}/bin/crayftn
        fc: /opt/cray/pe/cce/{x}/bin/crayftn
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
        return template.format(x=cce_version)

    def gcc_compiler_cfg(self, gcc_version):
        template = """\
compilers:                
  - compiler:
      spec: gcc@{x}
      paths:
        cc: /opt/cray/pe/gcc/{x}/bin/gcc
        cxx: /opt/cray/pe/gcc/{x}/bin/g++
        f77: /opt/cray/pe/gcc/{x}/bin/gfortran
        fc: /opt/cray/pe/gcc/{x}/bin/gfortran
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
        return template.format(x=gcc_version)

    def rocm_config(self, rocm_version):
        template = """\
packages:  
  comgr:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: comgr@{x}
  hip:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}/hip
      spec: hip@{x}
  hip-rocclr:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}/rocclr
      spec: hip-rocclr@{x}
  hipblas:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: hipblas@{x}
  hipcub:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: hipcub@{x}
  hipfft:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: hipfft@{x}
  hipfort:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: hipfort@{x}
  hipify-clang:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: hipify-clang@{x}
  hipsparse:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: hipsparse@{x}
  hsa-rocr-dev:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: hsa-rocr-dev@{x}
  hsakmt-roct:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: hsakmt-roct@{x}
  llvm-amdgpu:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}/llvm
      spec: llvm-amdgpu@{x}
  rccl:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rccl@{x}
  rocalution:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocalution@{x}
  rocblas:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocblas@{x}
  rocfft:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocfft@{x}
    variants: amdgpu_target=auto amdgpu_target_sram_ecc=auto
  rocm-clang-ocl:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocm-clang-ocl@{x}
  rocm-cmake:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocm-cmake@{x}
  rocm-device-libs:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocm-device-libs@{x}
  rocm-gdb:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocm-gdb@{x}
  rocm-opencl:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}/opencl
      spec: rocm-opencl@{x}
  rocm-opencl-runtime:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}/opencl
      spec: rocm-opencl-runtime@{x}
  rocm-openmp-extras:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}/llvm
      spec: rocm-openmp-extras@{x}
  rocm-smi:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}/rocm_smi
      spec: rocmsmi@{x}
  rocm-smi-lib:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}/rocm_smi
      spec: rocm-smi-lib@{x}
  rocminfo:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocminfo@{x}
  rocprim:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocprim@{x}
  rocprofiler-dev:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocprofiler-dev@{x}
  rocrand:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocrand@{x}
  rocsolver:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocsolver@{x}
  rocsparse:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocsparse@{x}
  rocthrust:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: rocthrust@{x}
  roctracer-dev:
    buildable: false
    externals:
    - prefix: /appl/lumi/SW/CrayEnv/EB/rocm/{x}
      spec: roctracer-dev@{x}
"""
        return template.format(x=rocm_version)

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
       pkg_spec: rocblas@5.6.1
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
