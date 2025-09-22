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
    variant("caliper", default=False, description="Enable Caliper monitoring")

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    depends_on("mpi", when="+mpi")
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")
    depends_on("hypre+caliper", when="+caliper")

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
            filter_file(r"^clang.*=.*", "clang =1", makefile)
        if spec.satisfies("%clang") or spec.satisfies("%gcc"):
            filter_file(r"^compiler.*=.*", f"compiler = {'openmpi-' if '+mpi' in spec else ''}gnu", makefile)
            filter_file(r"\s+CFLAGS\s+=.*", f"CFLAGS = -O3 -ffast-math -Wno-implicit-function-declaration", makefile)
        if spec.satisfies("%intel"):
            filter_file(r"^compiler.*=.*", "compiler = intel", makefile)
        if not spec.target == "a64fx":
            filter_file(r"^arch.*=.*", "arch = skylake", makefile)
            filter_file(r"-xCORE-AVX512", "-xHOST", makefile)
        if "+caliper" in spec:
            maincc = join_path(self.stage.source_path, "main.cc")
            filter_file(r"^profiler.*=.*", "profiler =caliper", makefile)
            filter_file(r"^clang.*=.*", "clang =1", makefile)
            filter_file(r"^ifeq \(\$\(profiler\),timing\)", "ifeq ($(profiler),caliper)\n  CFLAGS += -DUSE_CALIPER -I$(CALIPER_DIR)/include\n  LDFLAGS += -L$(CALIPER_DIR)/lib64 -lcaliper -Wl,-rpath,$(CALIPER_DIR)/lib64\nendif\nifeq ($(profiler),timing)", makefile)
            filter_file(r"^main\:\$\(OBJS\) \$\(MAIN\) \$\(LDFLAGS\)", "main:$(OBJS) $(MAIN)", makefile)
        #    filter_file(r"^#include <random>", "#include <random>\n#include <caliper/cali.h>", maincc)
        #    filter_file(r"\s+mt = std\:\:mt19937\(12345\);", f"mt = std::mt19937(12345);\n\n  CALI_MARK_BEGIN(\"main\");", maincc)
        #    filter_file(r"\s+PROF_FINALIZE", f"  PROF_FINALIZE;\n  CALI_MARK_END(\"main\")", maincc)
            qwscc = join_path(self.stage.source_path, "qws.cc")
            filter_file(r"^\#include \"timing.h\"", "extern \"C\"{\n#include \"timing.h\"\n}", qwscc)
            
            profiler = join_path(self.stage.source_path, "profiler.h")
            filter_file("\_FAPP","USE_CALIPER", profiler)
            
            filter_file(r"^\#include \<fj_tool\/fapp.h\>", "extern void cali_begin_region(const char*); extern void cali_end_region(const char*);", profiler)
            filter_file(r"^\#define PROF_START\(a\)     fapp_start\(a,1,0\);", "#define PROF_START(a)     cali_begin_region(a);", profiler)
            filter_file(r"^\#define PROF_STOP\(a\)      fapp_stop\(a,1,0\);", "#define PROF_STOP(a)     cali_end_region(a);", profiler)
            filter_file(r"^\#define PROF_START_SRL\(a\) fapp_start\(a,1,0\);", "#define PROF_START_SRL(a)     cali_begin_region(a);", profiler)
            filter_file(r"^\#define PROF_STOP_SRL\(a\)  fapp_stop\(a,1,0\);", "#define PROF_STOP_SRL(a)     cali_end_region(a);", profiler)

    @property
    def build_targets(self):
        targets = []
        spec = self.spec

        if "+caliper" in self.spec:
            targets.append("CALIPER_DIR=%s" % spec["caliper"].prefix)
            targets.append("ADIAK_DIR=%s" % spec["adiak"].prefix)

        return targets

    # See lib/spack/spack/build_systems/makefile.py
    def check(self):
        with working_dir(self.build_directory):
            make("tests", *self.build_targets)

    def install(self, spec, prefix):
        # QWS does not provide install target, so copy things into place.
        mkdirp(prefix.bin)
        install(join_path(self.build_directory, "main"), join_path(prefix.bin, "qws.exe"))
