# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class Commbench(CMakePackage, CudaPackage, ROCmPackage):
    """FIXME: Put a proper description of your package here."""

    # FIXME: Add a proper url for your package's homepage here.
    homepage = "https://github.com/simongdg/CommBench"
    # url = "https://github.com/arhag23/CommBench/archive/cmake.tar.gz"
    git = "https://github.com/simongdg/CommBench.git"
    
    version("0.1.0", commit="efed373")

    # FIXME: Add a list of GitHub accounts to
    # notify when the package is updated.
    maintainers("simongdg")

    # FIXME: Add the SPDX identifier of the project's license below.
    # See https://spdx.org/licenses/ for a list. Upon manually verifying
    # the license, set checked_by to your Github username.
    license("Apache-2.0", checked_by="simongdg")

    version("0.1.0")
    variant("cuda", default=False, description="Enable CUDA support")
    variant("rocm", default=False, description="Enable HIP support")
    variant("caliper", default=True, description="Enable Caliper profiling")

    # FIXME: Add dependencies if required.
    depends_on("c", type="build")
    depends_on("cxx", type="build")

    depends_on("cmake@3.24:", type="build")

    depends_on("mpi")

    depends_on("rccl", when="+rocm")
    depends_on("caliper", when="+caliper")

    for arch in ("none", "50", "60", "70", "80", "90"):
        depends_on(f"nccl cuda_arch={arch}", when=f"cuda_arch={arch}")

    def cmake_args(self):
        args = []
        # args.append("--debug-trycompile")
        if self.spec.satisfies("+rocm"):
            args.append("-DUSE_HIP=ON")
            args.append("-DUSE_XCCL=ON")
        elif self.spec.satisfies("+cuda"):
            args.append("-DUSE_CUDA=ON")
            args.append("-DUSE_XCCL=ON")

            cuda_arch = self.spec.variants["cuda_arch"].value[0]
            if cuda_arch is not None:
                args.append(f"-DCMAKE_CUDA_ARCHITECTURES={cuda_arch}")

        mpi_spec = self.spec["mpi"]

        if mpi_spec.satisfies("+gtl"):
            gtl_path = mpi_spec.extra_attributes["gtl_path"]
            args.append("-DUSE_GTL=ON")
            args.append(f"-DGTL_PATH={gtl_path}")
        
        if self.spec.satisfies("+caliper"):
            args.append("-DUSE_CALIPER=ON")
        
        return args
