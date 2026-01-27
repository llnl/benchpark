# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class Laghos(MakefilePackage, CudaPackage, ROCmPackage):
    """Laghos (LAGrangian High-Order Solver) is a CEED miniapp that solves the
    time-dependent Euler equations of compressible gas dynamics in a moving
    Lagrangian frame using unstructured high-order finite element spatial
    discretization and explicit high-order time-stepping.
    """

    tags = ["proxy-app", "ecp-proxy-app"]

    homepage = "https://github.com/CEED/Laghos"
    git = "https://github.com/CEED/Laghos.git"

    maintainers("wdhawkins")

    license("BSD-2-Clause")

    version("develop", branch="master")

    variant("metis", default=True, description="Enable/disable METIS support")
    variant("caliper", default=False, description="Enable/disable Caliper support")
    variant("ofast", default=False, description="Enable gcc optimization flags")
    variant("gpu-aware-mpi", default=False, description="Enable GPU aware MPI")

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    depends_on("mfem+mpi+metis", when="+metis")
    depends_on("mfem+mpi~metis", when="~metis")
    depends_on("caliper", when="+caliper")
    depends_on("adiak~shared", when="+caliper")

    depends_on("zlib+optimize+pic~shared")
    depends_on("mfem@develop", when="@develop")
    depends_on("mfem@4.2.0:", when="@3.1")
    depends_on("mfem@4.1.0:4.1", when="@3.0")
    # Recommended mfem version for laghos v2.0 is: ^mfem@3.4.1-laghos-v2.0
    depends_on("mfem@3.4.1-laghos-v2.0", when="@2.0")
    # Recommended mfem version for laghos v1.x is: ^mfem@3.3.1-laghos-v1.0
    depends_on("mfem@3.3.1-laghos-v1.0", when="@1.0,1.1")
    depends_on("mfem+caliper", when="+caliper")
    depends_on("mfem cxxstd=17")

    requires("^[virtuals=zlib-api] zlib")

    depends_on("mpi")
    depends_on("hypre+mpi")
    depends_on("hypre+cuda+mpi", when="+cuda")
    depends_on("hypre+mixedint~fortran", when="@develop")
    depends_on("hypre+caliper", when="+caliper")

    requires("+cuda", when="^hypre+cuda")
    for arch in ("none", "50", "60", "70", "80", "90"):
        depends_on(f"hypre cuda_arch={arch}", when=f"cuda_arch={arch}")
        depends_on(f"mfem cuda_arch={arch}", when=f"cuda_arch={arch}")
    depends_on("mfem +cuda+mpi", when="+cuda")
    depends_on("mfem +rocm+mpi", when="+rocm")
    depends_on("mfem +umpire", when="+cuda")
    depends_on("mfem +umpire", when="+rocm")

    depends_on("hypre +rocm+mpi", when="+rocm")
    requires("+rocm", when="^hypre+rocm")
    for target in ("none", "gfx803", "gfx900", "gfx906", "gfx908", "gfx90a", "gfx942"):
        depends_on(f"hypre amdgpu_target={target}", when=f"amdgpu_target={target}")
        depends_on(f"mfem amdgpu_target={target}", when=f"amdgpu_target={target}")

    depends_on("hypre+umpire", when="+cuda")
    depends_on("hypre+umpire", when="+rocm")
    depends_on("hypre+gpu-aware-mpi", when="+gpu-aware-mpi")

    # Replace MPI_Session
    patch(
        "https://github.com/CEED/Laghos/commit/c800883ab2741c8c3b99486e7d8ddd8e53a7cb95.patch?full_index=1",
        sha256="e783a71c3cb36886eb539c0f7ac622883ed5caf7ccae597d545d48eaf051d15d",
        when="@3.1 ^mfem@4.4:",
    )

    def setup_run_environment(self, env):
        if "+gpu-aware-mpi" in self.spec:
            env.set("MFEM_GPU_AWARE_MPI", "1")

    def setup_build_environment(self, env):
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    @property
    def build_targets(self):
        targets = []
        spec = self.spec

        targets.append("MFEM_DIR=%s" % spec["mfem"].prefix)
        targets.append("CONFIG_MK=%s" % spec["mfem"].package.config_mk)
        targets.append("TEST_MK=%s" % spec["mfem"].package.test_mk)
        if "+caliper" in self.spec:
            targets.append("USE_CALIPER=ON")
            targets.append("CALIPER_DIR=%s" % spec["caliper"].prefix)
            targets.append("ADIAK_DIR=%s" % spec["adiak"].prefix)
        if spec.satisfies("@:2.0"):
            targets.append("CXX=%s" % spec["mpi"].mpicxx)
        if self.spec.satisfies("+ofast %gcc"):
            targets.append("CXXFLAGS = -Ofast -finline-functions")
        return targets

    # See lib/spack/spack/build_systems/makefile.py
    def check(self):
        with working_dir(self.build_directory):
            make("test", *self.build_targets)

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        install("laghos", prefix.bin)
        install_tree("data", prefix.data)

    install_time_test_callbacks = []  # type: List[str]
