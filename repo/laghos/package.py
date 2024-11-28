# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class Laghos(MakefilePackage):
    """Laghos (LAGrangian High-Order Solver) is a CEED miniapp that solves the
    time-dependent Euler equations of compressible gas dynamics in a moving
    Lagrangian frame using unstructured high-order finite element spatial
    discretization and explicit high-order time-stepping.
    """

    tags = ["proxy-app", "ecp-proxy-app"]

    homepage = "https://github.com/wdhawkins/laghos"
    git = "https://github.com/wdhawkins/Laghos.git"

    maintainers("wdhawkins")

    license("BSD-2-Clause")

    version("develop", branch="caliper")

    variant("metis", default=True, description="Enable/disable METIS support")
    variant("caliper", default=False, description="Enable/disable Caliper support")
    variant("ofast", default=False, description="Enable gcc optimization flags")

    depends_on("mfem+mpi+metis", when="+metis")
    depends_on("mfem+mpi~metis", when="~metis")
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")

    depends_on("hypre~fortran", when="@develop")
    depends_on("zlib@1.3.1+optimize+pic+shared", when="@develop")
    depends_on("mfem@develop^zlib@1.3.1+optimize+pic+shared", when="@develop")
    depends_on("mfem@4.2.0:", when="@3.1")
    depends_on("mfem@4.1.0:4.1", when="@3.0")
    # Recommended mfem version for laghos v2.0 is: ^mfem@3.4.1-laghos-v2.0
    depends_on("mfem@3.4.1-laghos-v2.0", when="@2.0")
    # Recommended mfem version for laghos v1.x is: ^mfem@3.3.1-laghos-v1.0
    depends_on("mfem@3.3.1-laghos-v1.0", when="@1.0,1.1")

    # Replace MPI_Session
    patch(
        "https://github.com/CEED/Laghos/commit/c800883ab2741c8c3b99486e7d8ddd8e53a7cb95.patch?full_index=1",
        sha256="e783a71c3cb36886eb539c0f7ac622883ed5caf7ccae597d545d48eaf051d15d",
        when="@3.1 ^mfem@4.4:",
    )

    @property
    def build_targets(self):
        targets = []
        spec = self.spec

        targets.append("MFEM_DIR=%s" % spec["mfem"].prefix)
        targets.append("CONFIG_MK=%s" % spec["mfem"].package.config_mk)
        targets.append("TEST_MK=%s" % spec["mfem"].package.test_mk)
        if "+caliper" in self.spec: 
            targets.append("CALIPER_DIR=%s" % spec["caliper"].prefix)
        if spec.satisfies("@:2.0"):
            targets.append("CXX=%s" % spec["mpi"].mpicxx)
        if "+ofast %gcc" in self.spec:
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
