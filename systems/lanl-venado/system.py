# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from benchpark.directives import variant
from benchpark.system import System

id_to_resources = {
    "grace-hopper": {
        "sys_cores_per_node": 144,
        "sys_gpus_per_node": 4,
    },
    "grace-grace": {
        "sys_cores_per_node": 144,
    },
}


class LanlVenado(System):
    variant(
        "cluster",
        default="grace-hopper",
        values=("grace-hopper", "grace-grace"),
        description="Which cluster to run on",
    )

    variant(
        "cuda",
        default="12-5",
        values=("11.8", "12.5"),
        description="CUDA version",
    )

    variant(
        "compiler",
        default="cce",
        values=("gcc", "cce"),
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
        default="cusolver",
        values=("cusolver", "cray-libsci"),
        description="Which lapack to use",
    )

    variant(
        "blas",
        default="cublas",
        values=("cublas", "cray-libsci"),
        description="Which blas to use",
    )

    def initialize(self):
        super().initialize()

        self.scheduler = "slurm"
        attrs = id_to_resources.get(self.spec.variants["cluster"][0])
        for k, v in attrs.items():
            setattr(self, k, v)

    def generate_description(self, output_dir):
        super().generate_description(output_dir)

        sw_description = pathlib.Path(output_dir) / "software.yaml"

        with open(sw_description, "w") as f:
            f.write(self.sw_description())

    def system_specific_variables(self):
        return {
            "cuda_arch": "90",
            "default_cuda_version": self.spec.variants["cuda"][0],
            "extra_batch_opts": '"-A llnl_ai_g -pgpu"',
        }

    def external_pkg_configs(self):
        externals = LanlVenado.resource_location / "externals"

        selections = [externals / "base" / "00-packages.yaml"]

        cuda_cfg_path = self.next_adhoc_cfg()
        with open(cuda_cfg_path, "w") as f:
            f.write(self.cuda_config(self.spec.variants["cuda"][0]))
        selections.append(cuda_cfg_path)

        mpi_cfg_path = self.next_adhoc_cfg()
        with open(mpi_cfg_path, "w") as f:
            f.write(self.mpi_config())
        selections.append(mpi_cfg_path)

        if self.spec.satisfies("compiler=cce"):
            selections.append(externals / "libsci" / "01-cce-packages.yaml")
        elif self.spec.satisfies("compiler=gcc"):
            selections.append(externals / "libsci" / "00-gcc-packages.yaml")

        return selections

    def compiler_configs(self):
        compilers = LanlVenado.resource_location / "compilers"

        selections = []
        # TODO: Construct/extract/customize compiler information from the working set
        if self.spec.satisfies("compiler=cce"):
            selections.append(compilers / "cce" / "00-cce-18-compilers.yaml")
        selections.append(compilers / "gcc" / "00-gcc-12-compilers.yaml")

        return selections

    def mpi_config(self):
        mpi_version = "8.1.30"
        gtl = (
            "+gtl"
            if self.spec.satisfies("compiler=cce") and self.spec.satisfies("+gtl")
            else "~gtl"
        )

        # TODO: Construct/extract this information from the working set
        if self.spec.satisfies("compiler=cce"):
            compiler = "cce@18.0.0"
            mpi_compiler_suffix = "crayclang/17.0"
        elif self.spec.satisfies("compiler=gcc"):
            compiler = "gcc@12.3.0"
            mpi_compiler_suffix = "gnu/12.3"

        return f"""\
packages:
  cray-mpich:
    externals:
    - spec: cray-mpich@{mpi_version}%{compiler} {gtl} +wrappers
      prefix: /opt/cray/pe/mpich/{mpi_version}/ofi/{mpi_compiler_suffix}
      extra_attributes:
        gtl_lib_path: /opt/cray/pe/mpich/{mpi_version}/gtl/lib
        gtl_libs: ["libmpi_gtl_cuda"]
        ldflags: "-L/opt/cray/pe/mpich/{mpi_version}/ofi/{mpi_compiler_suffix}/lib -lmpi -L/opt/cray/pe/mpich/{mpi_version}/gtl/lib -Wl,-rpath=/opt/cray/pe/mpich/{mpi_version}/gtl/lib -lmpi_gtl_cuda"
"""

    def cuda_config(self, cuda_version):
        template = """\
packages:
  blas:
    require:
      - {blas}
  lapack:
    require:
      - {lapack}
  curand:
    externals:
    - spec: curand@{x}
      prefix: /opt/nvidia/hpc_sdk/Linux_aarch64/24.7/cuda/{x}
    buildable: false
  cusparse:
    externals:
    - spec: cusparse@{x}
      prefix: /opt/nvidia/hpc_sdk/Linux_aarch64/24.7/cuda/{x}
    buildable: false
  cuda:
    externals:
    - spec: cuda@{x}
      prefix: /opt/nvidia/hpc_sdk/Linux_aarch64/24.7/cuda/{x}
    buildable: false
  cub:
    externals:
    - spec: cub@{x}
      prefix: /opt/nvidia/hpc_sdk/Linux_aarch64/24.7/cuda/{x}
    buildable: false
  cublas:
    externals:
    - spec: cublas@{x}
      prefix: /opt/nvidia/hpc_sdk/Linux_aarch64/24.7/math_libs/{x}
    buildable: false
  cusolver:
    externals:
    - spec: cusolver@{x}
      prefix: /opt/nvidia/hpc_sdk/Linux_aarch64/24.7/math_libs/{x}
    buildable: false
  cufft:
    externals:
    - spec: cufft@{x}
      prefix: /opt/nvidia/hpc_sdk/Linux_aarch64/24.7/math_libs/{x}
    buildable: false
"""
        return template.format(
            x=cuda_version,
            blas=self.spec.variants["blas"][0],
            lapack=self.spec.variants["lapack"][0],
        )

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
      pkg_spec: {self.spec.variants["compiler"][0]}
    default-mpi:
      pkg_spec: cray-mpich
    default-lapack:
      pkg_spec: {self.spec.variants["lapack"][0]}
    default-blas:
      pkg_spec: {self.spec.variants["blas"][0]}
"""
