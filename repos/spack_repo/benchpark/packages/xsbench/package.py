# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.makefile import MakefilePackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage

from spack.package import *


class Xsbench(MakefilePackage, CudaPackage, ROCmPackage):
    """XSBench is a mini-app representing a key computational
    kernel of the Monte Carlo neutronics application OpenMC.
    A full explanation of the theory and purpose of XSBench
    is provided in docs/XSBench_Theory.pdf."""

    homepage = "https://github.com/ANL-CESAR/XSBench/"
    url = "https://github.com/ANL-CESAR/XSBench/archive/v13.tar.gz"
    git = "https://github.com/daboehme/XSBench.git"

    tags = ["proxy-app", "ecp-proxy-app"]

    version(
        "mpi-fix", git="https://github.com/RanivG/XSBench.git", branch="caliper-mpi-fixes"
    )

    version(
        "caliper-support", git="https://github.com/daboehme/XSBench.git", branch="caliper-support"
    )
    version(
        "20", sha256="3430328267432b4c29605f248809caec3e8b0e3442d4dcd672fa09b8bb9aa1b6"
    )
    version(
        "19", sha256="57cc44ae3b0a50d33fab6dd48da13368720d2aa1b91cde47d51da78bf656b97e"
    )
    version(
        "18", sha256="a9a544eeacd1be8d687080d2df4eeb701c04eda31d3806e7c3ea1ff36c26f4b0"
    )
    version(
        "14", sha256="595afbcba8c1079067d5d17eedcb4ab0c1d115f83fd6f8c3de01d74b23015e2d"
    )
    version(
        "13", sha256="b503ea468d3720a0369304924477b758b3d128c8074776233fa5d567b7ffcaa2"
    )

    variant("mpi", default=True, description="Build with MPI support")
    variant("openmp", default=False, description="Build with OpenMP support")
    variant("cuda", default=False, when="@19:", description="Build with CUDA support")
    variant(
        "rocm", default=False, when="@20:", description="Build worth ROCm/HIP support"
    )

    depends_on("c", type="build")  # generated
    depends_on("cxx", type="build")  # generated

    depends_on("mpi", when="+mpi")
    depends_on("caliper", when="@mpi-fix")
    depends_on("caliper+rocm amdgpu_target=gfx942", when="@caliper-support:+rocm")
    depends_on("adiak", when="@mpi-fix")

    conflicts("+cuda", when="+rocm", msg="CUDA and ROCm are mutually exclusive")
    conflicts("cuda_arch=none", when="+cuda", msg="Must select a CUDA architecture")
    conflicts("+cuda", when="+openmp", msg="OpenMP must be disabled to support CUDA")
    conflicts("+rocm", when="+openmp", msg="OpenMP must be disabled to support ROCm")

    @property
    def build_directory(self):
        # if self.spec.satisfies("@:18"):
        #     return "src"

        # if "+openmp" in self.spec:
        #     return "openmp-threading"

        if "+cuda" in self.spec:
            return "cuda"

        elif "+rocm" in self.spec:
            return "hip"

        else:
            return "openmp-threading"

    @property
    def build_targets(self):
        targets = []
        cflags = ""

        if "@caliper-support" in self.spec:
            targets.append("CALI_DIR={0}".format(self.spec["caliper"].prefix))
            targets.append("ADIAK_DIR={0}".format(self.spec["adiak"].prefix))

        if "+cuda" in self.spec:
            return ["SM_VERSION={0}".format(self.spec.variants["cuda_arch"].value[0])]

        if "+rocm" in self.spec:
            amdgpu_targets = self.spec.variants["amdgpu_target"].value
            hip_flags = self.hip_flags(amdgpu_targets)
            #return ["CFLAGS={0} -std=c++14 -O3".format(hip_flags)]

        if not self.spec.satisfies("%nvhpc@:20.11"):
            cflags = "-std=gnu99"

        if "+mpi" in self.spec:
            # targets.append("CC={0}".format(self.spec["mpi"].mpicc))
            targets.append("MPI=yes")
        else:
            # targets.append("CC={0}".format(self.compiler.cc))
            targets.append("MPI=no")

        if "+openmp" in self.spec:
            cflags += " " + self.compiler.openmp_flag
        # targets.append("CFLAGS={0}".format(cflags))
        # targets.append("LDFLAGS=-lm")

        return targets

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        with working_dir(self.build_directory):
            install("XSBench", prefix.bin)
