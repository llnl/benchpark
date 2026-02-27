# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class MpiPingpong(CMakePackage, ROCmPackage, CudaPackage):

    git = "https://github.com/LLNL/microbenchmarks.git"

    version("develop", branch="develop")

    variant("caliper", default=False, description="Enable Caliper/Adiak support")
    variant("rocm", default=False, description="Enable Rocm support")
    variant("cuda", default=False, description="Enable CUDA support")
    variant("mpi", default=True, description="Enable MPI support")

    depends_on("mpi", when="+mpi")
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")
    depends_on("hip", when="+rocm")
    depends_on("cuda", when="+cuda")

    conflicts("+cuda +rocm", msg="Enable only one of +cuda or +rocm")

    root_cmakelists_dir = "repo/pingpong"

    def cmake_args(self):
        if self.spec.satisfies("+caliper"):
            args = ["-DUSE_CALIPER=ON"]
        else:
            args = ["-DUSE_CALIPER=OFF"]

        if self.spec.satisfies("+rocm"):
            args.append(
                self.define("CMAKE_EXE_LINKER_FLAGS", self.spec["mpi"].libs.ld_flags)
            )
            args.append("-DUSE_HIP=ON")
            args.append(self.define("ROCM_PATH", self.spec["hip"].prefix))
            hip_vars = self.spec["hip"].variants
            if "amdgpu_targets" in hip_vars:
                vals = [t for t in hip_vars["amdgpu_targets"].value if t != "none"]
                if vals:
                    archs = ",".join(vals)
                    args.append(self.define("CMAKE_HIP_ARCHITECTURES", archs))
        else:
            args.append("-DUSE_HIP=OFF")

        if self.spec.satisfies("+cuda"):
            args.append(self.define("USE_CUDA", "ON"))
            v = self.spec.variants.get("cuda_arch", None)
            if v:
                vals = [a for a in v.value if a != "none"]
                if vals:
                    args.append(self.define("CMAKE_CUDA_ARCHITECTURES", ";".join(vals)))
        else:
            args.append(self.define("USE_CUDA", "OFF"))

        return args

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        install(join_path(self.build_directory, "pingpong"), prefix.bin)
