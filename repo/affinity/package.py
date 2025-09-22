# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class Affinity(CMakePackage, CudaPackage, ROCmPackage):
    """Simple applications for determining Linux thread and gpu affinity."""

    homepage = "https://github.com/bcumming/affinity"
    git = "https://github.com/bcumming/affinity.git"
    version("master", branch="master")

    maintainers("bcumming", "nhanford")

    license("BSD-3-Clause", checked_by="nhanford")

    variant("mpi", default=False, description="Build MPI support")
    variant("rocm", default=False, description="Build ROCm Support")

    depends_on("c", type="build")
    depends_on("cxx", type="build")

    depends_on("mpi", when="+mpi")
    depends_on("hip", when="+rocm")
    depends_on("cuda", when="+cuda")

    def cmake_args(self):
        spec = self.spec
        args = []

        if '+mpi' in spec:
            args.append('-DCMAKE_CXX_COMPILER={0}'.format(spec["mpi"].mpicxx))
            args.append("-DMPI_CXX_LINK_FLAGS={0}".format(spec["mpi"].libs.ld_flags))
            args.append("-DAFFINITY_MPI=on")

        if '+cuda' in spec:
            args.append('-DCMAKE_CUDA_HOST_COMPILER={0}'.format(spec["mpi"].mpicxx))
            args.append('-DCMAKE_CUDA_COMPILER={0}'.format(spec["cuda"].prefix + "/bin/nvcc"))
            args.append("-DAFFINITY_GPU_BACKEND=cuda")

        if '+rocm' in spec:
            args.append("-DROCM_PATH={0}".format(spec['hip'].prefix))
            args.append("-DAFFINITY_GPU_BACKEND=rocm")
            rocm_archs = spec.variants["amdgpu_target"].value
            if "none" not in rocm_archs:
                args.append("-DHIP_HIPCC_FLAGS=--amdgpu-target={0}".format(",".join(rocm_archs)))
                args.append("-DCMAKE_HIP_ARCHITECTURES={0}".format(rocm_archs))

        return args
