# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class Qws(MakefilePackage):
    """QWS benchmark for Lattice quantum chromodynamics simulation library for
    Fugaku and computers with wide SIMD"""

    homepage = "https://www.riken.jp/en/research/labs/r-ccs/field_theor/index.html"
    git = "https://github.com/RIKEN-LQCD/qws.git"

    version("master", branch="master", submodules=False)

    variant("mpi", default=True, description="Build with MPI.")
    variant("openmp", default=True, description="Build with OpenMP enabled.")

    depends_on("mpi", when="+mpi")

    def edit(self, spec, prefix):
        makefile = join_path(self.stage.source_path, "Makefile")
        if "+mpi" not in spec:
            filter_file("^mpi", "#mpi", makefile)
            filter_file(r"\s+CC\s+=.*", f"CC = {spack_cc}", makefile)
            filter_file(r"\s+CXX\s+=.*", f"CXX = {spack_cxx}", makefile)
            filter_file(r"\s+F90\s+=.*", f"F90 = {spack_fc}", makefile)
        else:
            filter_file(r"\s+CC\s+=.*", f"CC = {spec['mpi'].mpicc}", makefile)
            filter_file(r"\s+CXX\s+=.*", f"CXX = {spec['mpi'].mpicxx}", makefile)
            filter_file(r"\s+F90\s+=.*", f"F90 = {spec['mpi'].mpifc}", makefile)
            filter_file(r"^rdma.*=.*", "rdma =", makefile)
        if "+openmp" not in spec:
            filter_file("^omp", "#omp", makefile)
        if spec.satisfies("%fj"):
            filter_file(r"^compiler.*=.*", "compiler = fujitsu_native", makefile)
        if spec.satisfies("%clang") or spec.satisfies("%gcc"):
            filter_file(r"^compiler.*=.*", f"compiler = {'openmpi-' if '+mpi' in spec else ''}gnu", makefile)
            filter_file(r"\s+CFLAGS\s+=.*", f"CFLAGS = -O3 -ffast-math -Wno-implicit-function-declaration", makefile)
        if spec.satisfies("%intel"):
            filter_file(r"^compiler.*=.*", "compiler = intel", makefile)
        if not spec.target == "a64fx":
            filter_file(r"^arch.*=.*", "arch = skylake", makefile)
            filter_file(r"-xCORE-AVX512", "-xHOST", makefile)

    def install(self, spec, prefix):
        # QWS does not provide install target, so copy things into place.
        mkdirp(prefix.bin)
        install(join_path(self.build_directory, "main"), join_path(prefix.bin, "qws.exe"))
