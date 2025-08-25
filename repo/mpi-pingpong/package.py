# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class MpiPingpong(CMakePackage, ROCmPackage):

    git = "https://github.com/LLNL/microbenchmarks.git"

    version("develop", branch="addHip")

    variant("caliper", default=False, description="Enable Caliper/Adiak support")
    variant("rocm", default=True, description="Enable Rocm support")

    depends_on("mpi")
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")
    depends_on("hip", when="+rocm")

    root_cmakelists_dir = "repo/pingpong"

    def cmake_args(self):
        if self.spec.satisfies("+caliper"):
            args = [
                "-DUSE_CALIPER=ON"
            ]
        else:
            args = [
                "-DUSE_CALIPER=OFF"
            ]

        if '+rocm' in self.spec:
            if self.spec.satisfies("+rocm"):
                args.append(self.define("CMAKE_EXE_LINKER_FLAGS", self.spec['mpi'].libs.ld_flags))
                args.append('-DUSE_ROCM=ON')
                args.append(self.define("ROCM_PATH", self.spec["hip"].prefix))
                hip_vars = self.spec["hip"].variants
            if "amdgpu_targets" in hip_vars:
                vals = [t for t in hip_vars["amdgpu_targets"].value if t != "none"]
                if vals:
                    archs = ",".join(vals)
                    args.append(self.define("CMAKE_HIP_ARCHITECTURES", archs))
        else:
            args.append('-DUSE_ROCM=OFF')
        
        return args
        
    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        install(join_path(self.build_directory, "pingpong"), prefix.bin)
