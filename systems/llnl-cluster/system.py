# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from benchpark.directives import variant
from benchpark.system import System

id_to_resources = {
    "ruby": {
        "scheduler": "slurm",
        "sys_cores_per_node": 56,
    },
    "magma": {
        "scheduler": "slurm",
        "sys_cores_per_node": 96,
    },
    "dane": {
        "scheduler": "slurm",
        "sys_cores_per_node": 112,
    },
    "corona": {
        "scheduler": "flux",
        "sys_cores_per_node": 96,
        "sys_gpus_per_node": 8,
    },
}


class LlnlCluster(System):

    variant(
        "cluster",
        default="ruby",
        values=("ruby", "magma", "dane", "corona"),
        description="Which cluster to run on",
    )

    variant(
        "compiler",
        default="gcc",
        values=("gcc", "intel"),
        description="Which compiler to use",
    )

    variant(
        "lapack",
        default="intel-oneapi-mkl",
        description="Which lapack to use",
    )

    variant(
        "blas",
        default="intel-oneapi-mkl",
        description="Which blas to use",
    )
    
    variant(
        "rocm",
        default="6.0.2",
        values=("5.4.3", "5.5.1", "5.6.1", "5.7.1", "6.0.2"),
        when="cluster=corona",
        description="ROCm version",
    )

    def initialize(self):
        super().initialize()

        attrs = id_to_resources.get(self.spec.variants["cluster"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def generate_description(self, output_dir):
        super().generate_description(output_dir)

        sw_description = pathlib.Path(output_dir) / "software.yaml"

        with open(sw_description, "w") as f:
            f.write(self.sw_description())

    def rocm_config(self, rocm_version):
        template = """\
packages:
  hipfft:
    externals:
    - spec: hipfft@{x}
      prefix: /opt/rocm-{x}
  rocfft:
    externals:
    - spec: rocfft@{x}
      prefix: /opt/rocm-{x}
  rocprim:
    externals:
    - spec: rocprim@{x}
      prefix: /opt/rocm-{x}
  rocrand:
    externals:
    - spec: rocrand@{x}
      prefix: /opt/rocm-{x}/hiprand
  rocsparse:
    externals:
    - spec: rocsparse@{x}
      prefix: /opt/rocm-{x}
  rocthrust:
    externals:
    - spec: rocthrust@{x}
      prefix: /opt/rocm-{x}
  hip:
    externals:
    - spec: hip@{x}
      prefix: /opt/rocm-{x}
  hsa-rocr-dev:
    externals:
    - spec: hsa-rocr-dev@{x}
      prefix: /opt/rocm-{x}
  comgr:
    externals:
    - spec: comgr@{x}
      prefix: /opt/rocm-{x}/
  hipsparse:
    externals:
    - spec: hipsparse@{x}
      prefix: /opt/rocm-{x}
  hipblas:
    externals:
    - spec: hipblas@{x}
      prefix: /opt/rocm-{x}/
  hsakmt-roct:
    externals:
    - spec: hsakmt-roct@{x}
      prefix: /opt/rocm-{x}/
  roctracer-dev-api:
    externals:
    - spec: roctracer-dev-api@{x}
      prefix: /opt/rocm-{x}/
  rocminfo:
    externals:
    - spec: rocminfo@{x}
      prefix: /opt/rocm-{x}/
  llvm:
    externals:
    - spec: llvm@16.0.0
      prefix: /opt/rocm-{x}/llvm
  llvm-amdgpu:
    externals:
    - spec: llvm-amdgpu@{x}
      prefix: /opt/rocm-{x}/llvm
  rocblas:
    externals:
    - spec: rocblas@{x}
      prefix: /opt/rocm-{x}
  rocsolver:
    externals:
    - spec: rocsolver@{x}
      prefix: /opt/rocm-{x}
"""
        return template.format(x=rocm_version)

    def external_pkg_configs(self):
        externals = LlnlCluster.resource_location / "externals"

        selections = [externals / "base" / "00-packages.yaml"]

        if self.spec.satisfies("cluster=corona"):
            rocm_cfg_path = self.next_adhoc_cfg()
            with open(rocm_cfg_path, "w") as f:
                f.write(self.rocm_config(self.spec.variants["rocm"][0]))
            selections.append(rocm_cfg_path)

        if self.spec.satisfies("compiler=gcc"):
            selections.append(externals / "mpi" / "00-gcc-packages.yaml")
        elif self.spec.satisfies("compiler=intel"):
            selections.append(externals / "mpi" / "01-intel-packages.yaml")

        return selections

    def rocm_compiler_cfg(self, rocm_version):
        template = """\
compilers:
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
      prepend_path:
        LIBRARY_PATH: /opt/rocm-{x}/lib
    extra_rpaths:
    - /opt/rocm-{x}/lib
"""
        return template.format(x=rocm_version)

    def compiler_configs(self):
        compilers = LlnlCluster.resource_location / "compilers"

        selections = []
        if self.spec.satisfies("compiler=gcc"):
            selections.append(compilers / "gcc" / "00-gcc-12-compilers.yaml")
        elif self.spec.satisfies("compiler=intel"):
            selections.append(compilers / "intel" / "00-intel-2021-6-0-compilers.yaml")

        if self.spec.satisfies("cluster=corona"):
            compiler_cfg_path = self.next_adhoc_cfg()
            with open(compiler_cfg_path, "w") as f:
                f.write(self.rocm_compiler_cfg(self.spec.variants["rocm"][0]))
            selections.append(compiler_cfg_path)

        return selections

    def sw_description(self):
        """This is somewhat vestigial, and maybe deleted later. The experiments
        will fail if these variables are not defined though, so for now
        they are still generated (but with more-generic values).
        """
        extra_software = ""
        if self.spec.satisfies("cluster=corona"):
            base_indent = " " * 2
            package_indent = " " * 4
            corona_extras = [
                f"blas-rocm:\n{package_indent}{base_indent}pkg_spec: rocblas",
                f"lapack-rocm:\n{package_indent}{base_indent}pkg_spec: rocsolver",
                f"compiler-amdclang:\n{package_indent}{base_indent}pkg_spec: clang"
            ]
            extra_software = f"\n{package_indent}".join(corona_extras)
        return f"""\
software:
  packages:
    default-compiler:
      pkg_spec: gcc
    default-mpi:
      pkg_spec: mvapich2
    default-lapack:
      pkg_spec: {self.spec.variants["lapack"][0]}
    default-blas:
      pkg_spec: {self.spec.variants["blas"][0]}
    compiler-gcc:
      pkg_spec: gcc
    compiler-intel:
      pkg_spec: intel
    blas:
      pkg_spec: intel-oneapi-mkl
    lapack:
      pkg_spec: intel-oneapi-mkl
    mpi-gcc:
      pkg_spec: mvapich2
    mpi-intel:
      pkg_spec: mvapich2
    {extra_software}
"""
