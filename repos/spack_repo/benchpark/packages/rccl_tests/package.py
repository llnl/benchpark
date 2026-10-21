# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage

from spack.package import *


class RcclTests(CMakePackage, ROCmPackage):
    """These tests check both the performance and the correctness of RCCL
    operations. They can be compiled against RCCL."""

    homepage = "https://github.com/ROCm/rocm-systems/tree/develop/projects/rccl-tests"
    git = "https://github.com/ROCm/rocm-systems.git"
    url = "https://github.com/ROCm/rocm-systems/archive/refs/heads/develop.tar.gz"
    root_cmakelists_dir = "projects/rccl-tests"
    tags = ["rocm"]

    maintainers("michaelmckinsey1")

    license("BSD-3-Clause")

    version("develop", branch="develop", preferred=True)
    # Retain master as a compatibility alias for the develop branch.
    version("master", branch="develop")

    variant("mpi", default=True, description="with MPI support")

    depends_on("cxx", type="build")
    requires("%cxx=llvm-amdgpu", msg="rccl-tests builds only with llvm-amdgpu")

    depends_on("hip")
    depends_on("rccl")
    depends_on("mpi", when="+mpi")

    conflicts("~rocm", msg="rccl-tests requires ROCm")

    def setup_run_environment(self, env):
        # Each rank sees its assigned GPU as device 0.
        env.set("NCCL_TESTS_DEVICE", "0")

    def cmake_args(self):
        args = [
            self.define("EXPLICIT_ROCM_VERSION", self.spec["hip"].version),
            self.define("ROCM_PATH", self.spec["hip"].prefix),
            self.define("RCCL_ROOT", self.spec["rccl"].prefix),
            self.define_from_variant("USE_MPI", "mpi"),
        ]
        targets = self.spec.variants["amdgpu_target"].value
        if targets:
            args.append(self.define("GPU_TARGETS", ";".join(targets)))
        return args
