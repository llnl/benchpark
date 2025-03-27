# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import glob
import os
import re
import socket
from os import environ as env
from os.path import join as pjoin

from spack import *


def spec_uses_toolchain(spec):
    gcc_toolchain_regex = re.compile(".*gcc-toolchain.*")
    using_toolchain = list(filter(gcc_toolchain_regex.match, spec.compiler_flags["cxxflags"]))
    return using_toolchain

def spec_uses_gccname(spec):
    gcc_name_regex = re.compile(".*gcc-name.*")
    using_gcc_name = list(filter(gcc_name_regex.match, spec.compiler_flags["cxxflags"]))
    return using_gcc_name

def hip_repair_options(options, spec):
    # there is only one dir like this, but the version component is unknown
    options.append(
        "-DHIP_CLANG_INCLUDE_PATH="
        + glob.glob("{}/lib/clang/*/include".format(spec["llvm-amdgpu"].prefix))[0]
    )

def hip_repair_cache(options, spec):
    # there is only one dir like this, but the version component is unknown
    options.append(
        cmake_cache_path(
            "HIP_CLANG_INCLUDE_PATH",
            glob.glob("{}/lib/clang/*/include".format(spec["llvm-amdgpu"].prefix))[0],
        )
    )

def hip_for_radiuss_projects(options, spec, spec_compiler):
    # Here is what is typically needed for radiuss projects when building with rocm
    hip_root = spec["hip"].prefix
    rocm_root = hip_root + "/.."
    options.append(cmake_cache_path("HIP_ROOT_DIR", hip_root))
    options.append(cmake_cache_path("ROCM_ROOT_DIR", rocm_root))

    hip_repair_cache(options, spec)

    archs = spec.variants["amdgpu_target"].value
    if archs != "none":
        arch_str = ",".join(archs)
        options.append(
            cmake_cache_string("AMDGPU_TARGETS", "{0}".format(arch_str))
        )
        options.append(
            cmake_cache_string("HIP_HIPCC_FLAGS", "--amdgpu-target={0}".format(arch_str))
        )
        options.append(
            cmake_cache_string("CMAKE_HIP_ARCHITECTURES", arch_str)
        )

    # adrienbernede-22-11:
    #   Specific to Umpire, attempt port to RAJA and CHAI
    hip_link_flags = ""
    if "%gcc" in spec or spec_uses_toolchain(spec):
        if "%gcc" in spec:
            gcc_bin = os.path.dirname(spec_compiler.cxx)
            gcc_prefix = join_path(gcc_bin, "..")
        else:
            gcc_prefix = spec_uses_toolchain(spec)[0]
        options.append(cmake_cache_string("HIP_CLANG_FLAGS", "--gcc-toolchain={0}".format(gcc_prefix)))
        options.append(cmake_cache_string("CMAKE_EXE_LINKER_FLAGS", hip_link_flags + " -Wl,-rpath {}/lib64".format(gcc_prefix)))
    else:
        options.append(cmake_cache_string("CMAKE_EXE_LINKER_FLAGS", "-Wl,-rpath={0}/llvm/lib/".format(rocm_root)))

def cuda_for_radiuss_projects(options, spec):
    # Here is what is typically needed for radiuss projects when building with cuda

    cuda_flags = []
    if not spec.satisfies("cuda_arch=none"):
        cuda_arch = spec.variants["cuda_arch"].value
        cuda_flags.append("-arch sm_{0}".format(cuda_arch[0]))
        options.append(
            cmake_cache_string("CUDA_ARCH", "sm_{0}".format(cuda_arch[0])))
        options.append(
            cmake_cache_string("CMAKE_CUDA_ARCHITECTURES", "{0}".format(cuda_arch[0])))
    if spec_uses_toolchain(spec):
        cuda_flags.append("-Xcompiler {}".format(spec_uses_toolchain(spec)[0]))
    if (spec.satisfies("%gcc@8.1: target=ppc64le")):
        cuda_flags.append("-Xcompiler -mno-float128")
    options.append(cmake_cache_string("CMAKE_CUDA_FLAGS", " ".join(cuda_flags)))

def blt_link_helpers(options, spec, spec_compiler):

    ### From local package:
    fortran_compilers = ["gfortran", "xlf"]
    if any(compiler in spec_compiler.fc for compiler in fortran_compilers) and ("clang" in spec_compiler.cxx):
        # Pass fortran compiler lib as rpath to find missing libstdc++
        libdir = os.path.join(os.path.dirname(
                       os.path.dirname(spec_compiler.fc)), "lib")
        flags = ""
        for _libpath in [libdir, libdir + "64"]:
            if os.path.exists(_libpath):
                flags += " -Wl,-rpath,{0}".format(_libpath)
        description = ("Adds a missing libstdc++ rpath")
        if flags:
            options.append(cmake_cache_string("BLT_EXE_LINKER_FLAGS", flags, description))

        # Ignore conflicting default gcc toolchain
        options.append(cmake_cache_string("BLT_CMAKE_IMPLICIT_LINK_DIRECTORIES_EXCLUDE",
        "/usr/tce/packages/gcc/gcc-4.9.3/lib64;/usr/tce/packages/gcc/gcc-4.9.3/gnu/lib64/gcc/powerpc64le-unknown-linux-gnu/4.9.3;/usr/tce/packages/gcc/gcc-4.9.3/gnu/lib64;/usr/tce/packages/gcc/gcc-4.9.3/lib64/gcc/x86_64-unknown-linux-gnu/4.9.3"))

    compilers_using_toolchain = ["pgi", "xl", "icpc"]
    if any(compiler in spec_compiler.cxx for compiler in compilers_using_toolchain):
        if spec_uses_toolchain(spec) or spec_uses_gccname(spec):

            # Ignore conflicting default gcc toolchain
            options.append(cmake_cache_string("BLT_CMAKE_IMPLICIT_LINK_DIRECTORIES_EXCLUDE",
            "/usr/tce/packages/gcc/gcc-4.9.3/lib64;/usr/tce/packages/gcc/gcc-4.9.3/gnu/lib64/gcc/powerpc64le-unknown-linux-gnu/4.9.3;/usr/tce/packages/gcc/gcc-4.9.3/gnu/lib64;/usr/tce/packages/gcc/gcc-4.9.3/lib64/gcc/x86_64-unknown-linux-gnu/4.9.3"))

class RajaPerf(CachedCMakePackage, CudaPackage, ROCmPackage):
    """RAJA Performance Suite."""

    homepage = "http://software.llnl.gov/RAJAPerf/"
    git      = "https://github.com/LLNL/RAJAPerf.git"

    version("develop", branch="develop", submodules="True")
    version("main",  branch="main",  submodules="True")
    version("2022.10.0", tag="v2022.10.0", submodules="True")
    version("0.12.0", tag="v0.12.0", submodules="True")
    version("0.11.0", tag="v0.11.0", submodules="True")
    version("0.10.0", tag="v0.10.0", submodules="True")
    version("0.9.0", tag="v0.9.0", submodules="True")
    version("0.8.0", tag="v0.8.0", submodules="True")
    version("0.7.0", tag="v0.7.0", submodules="True")
    version("0.6.0", tag="v0.6.0", submodules="True")
    version("0.5.2", tag="v0.5.2", submodules="True")
    version("0.5.1", tag="v0.5.1", submodules="True")
    version("0.5.0", tag="v0.5.0", submodules="True")
    version("0.4.0", tag="v0.4.0", submodules="True")

    variant("mpi", default=True, description="Enable MPI support")
    variant("openmp", default=True, description="Build OpenMP backend")
    variant("openmp_target", default=False, description="Build with OpenMP target support")
    variant("shared", default=False, description="Build Shared Libs")
    variant("libcpp", default=False, description="Uses libc++ instead of libstdc++")
    variant("tests", default="basic", values=("none", "basic", "benchmarks"),
            multi=False, description="Tests to run")
    variant("caliper",default=False, description="Build with support for Caliper based profiling")

    depends_on("blt")
    depends_on("blt@0.5.2:", type="build", when="@2022.10.0:")
    depends_on("blt@0.5.0:", type="build", when="@0.12.0:")
    depends_on("blt@0.4.1:", type="build", when="@0.11.0:")
    depends_on("blt@0.4.0:", type="build", when="@0.8.0:")
    depends_on("blt@0.3.0:", type="build", when="@:0.7.0")

    depends_on("cmake@3.20:", when="@0.12.0:", type="build")
    depends_on("cmake@3.23:", when="@0.12.0: +rocm", type="build")
    depends_on("cmake@3.23:", when="@0.12.0: +cuda")
    depends_on("cmake@3.14:", when="@:0.12.0", type="build")

    depends_on("llvm-openmp", when="+openmp %apple-clang")

    depends_on("rocprim", when="+rocm")



    conflicts("~openmp", when="+openmp_target", msg="OpenMP target requires OpenMP")
    conflicts("+cuda", when="+openmp_target", msg="Cuda may not be activated when openmp_target is ON")

    depends_on("caliper", when="+caliper")
    depends_on("adiak@0.4:", when="+caliper")

    depends_on("mpi", when="+mpi")

    def _get_sys_type(self, spec):
        sys_type = str(spec.architecture)
        # if on llnl systems, we can use the SYS_TYPE
        if "SYS_TYPE" in env:
            sys_type = env["SYS_TYPE"]
        return sys_type

    @property
    # TODO: name cache file conditionally to cuda and libcpp variants
    def cache_name(self):
        hostname = socket.gethostname()
        if "SYS_TYPE" in env:
            hostname = hostname.rstrip("1234567890")
        var=""
        if "+cuda" in self.spec:
            var= "-".join([var,"cuda"])
        if "+libcpp" in self.spec:
            var="-".join([var,"libcpp"])

        return "{0}-{1}{2}-{3}@{4}-{5}.cmake".format(
            hostname,
            self._get_sys_type(self.spec),
            var,
            self.spec.compiler.name,
            self.spec.compiler.version,
            self.spec.dag_hash(8)
        )

    def initconfig_compiler_entries(self):
        spec = self.spec
        compiler = self.compiler
        # Default entries are already defined in CachedCMakePackage, inherit them:
        entries = super(RajaPerf, self).initconfig_compiler_entries()

        # Switch to hip as a CPP compiler.
        # adrienbernede-22-11:
        #   This was only done in upstream Spack raja package.
        #   I could not find the equivalent logic in Spack source, so keeping it.
        #if "+rocm" in spec:
        #    entries.insert(0, cmake_cache_path("CMAKE_CXX_COMPILER", spec["hip"].hipcc))

        # Override CachedCMakePackage CMAKE_C_FLAGS and CMAKE_CXX_FLAGS add
        # +libcpp specific flags
        flags = spec.compiler_flags

        # use global spack compiler flags
        cppflags = " ".join(flags["cppflags"])
        if cppflags:
            # avoid always ending up with " " with no flags defined
            cppflags += " "

        cflags = cppflags + " ".join(flags["cflags"])
        if "+libcpp" in spec:
            cflags += " ".join([cflags,"-DGTEST_HAS_CXXABI_H_=0"])
        if cflags:
            entries.append(cmake_cache_string("CMAKE_C_FLAGS", cflags))

        cxxflags = cppflags + " ".join(flags["cxxflags"])
        if "+libcpp" in spec:
            cxxflags += " ".join([cxxflags,"-stdlib=libc++ -DGTEST_HAS_CXXABI_H_=0"])
        if cxxflags:
            entries.append(cmake_cache_string("CMAKE_CXX_FLAGS", cxxflags))

        blt_link_helpers(entries, spec, compiler)

        # adrienbernede-23-01
        # Maybe we want to share this in the above blt_link_helpers function.
        compilers_using_cxx14 = ["intel-17", "intel-18", "xl"]
        if any(compiler in self.compiler.cxx for compiler in compilers_using_cxx14):
            entries.append(cmake_cache_string("BLT_CXX_STD", "c++14"))

        return entries

    def initconfig_hardware_entries(self):
        spec = self.spec
        compiler = self.compiler
        entries = super(RajaPerf, self).initconfig_hardware_entries()

        entries.append(cmake_cache_option("ENABLE_OPENMP", "+openmp" in spec))

        entries.append(cmake_cache_option("ENABLE_MPI", "+mpi" in spec))
        if "+mpi" in spec:
            entries.append(cmake_cache_string("MPI_CXX_COMPILER", spec["mpi"].mpicxx))

        # T benefit from the shared function "cuda_for_radiuss_projects",
        # we do not modify CMAKE_CUDA_FLAGS: it is already appended by the
        # shared function.
        if "+cuda" in spec:
            entries.append(cmake_cache_option("ENABLE_CUDA", True))
            # Shared handling of cuda.
            cuda_for_radiuss_projects(entries, spec)

            # Custom options. We place everything in CMAKE_CUDA_FLAGS_(RELEASE|RELWITHDEBINFO|DEBUG) which are not set by cuda_for_radiuss_projects
            if ("xl" in self.compiler.cxx):
                all_targets_flags = "-Xcompiler -qstrict -Xcompiler -qxlcompatmacros -Xcompiler -qalias=noansi" \
                                  + "-Xcompiler -qsmp=omp -Xcompiler -qhot -Xcompiler -qnoeh" \
                                  + "-Xcompiler -qsuppress=1500-029 -Xcompiler -qsuppress=1500-036" \
                                  + "-Xcompiler -qsuppress=1500-030" \

                cuda_release_flags = "-O3 -Xcompiler -O2 " + all_targets_flags
                cuda_reldebinf_flags = "-O3 -g -Xcompiler -O2 " + all_targets_flags
                cuda_debug_flags = "-O0 -g -Xcompiler -O2 " + all_targets_flags

            elif ("gcc" in self.compiler.cxx):
                all_targets_flags = "-Xcompiler -finline-functions -Xcompiler -finline-limit=20000"

                cuda_release_flags = "-O3 -Xcompiler -Ofast " + all_targets_flags
                cuda_reldebinf_flags = "-O3 -g -Xcompiler -Ofast " + all_targets_flags
                cuda_debug_flags = "-O0 -g -Xcompiler -O0 " + all_targets_flags

            else:
                all_targets_flags = "-Xcompiler -finline-functions"

                cuda_release_flags = "-O3 -Xcompiler -Ofast " + all_targets_flags
                cuda_reldebinf_flags = "-O3 -g -Xcompiler -Ofast " + all_targets_flags
                cuda_debug_flags = "-O0 -g -Xcompiler -O0 " + all_targets_flags

            entries.append(cmake_cache_string("CMAKE_CUDA_FLAGS_RELEASE", cuda_release_flags))
            entries.append(cmake_cache_string("CMAKE_CUDA_FLAGS_RELWITHDEBINFO", cuda_reldebinf_flags))
            entries.append(cmake_cache_string("CMAKE_CUDA_FLAGS_DEBUG", cuda_debug_flags))

        else:
            entries.append(cmake_cache_option("ENABLE_CUDA", False))

        if "+rocm" in spec:
            entries.append(cmake_cache_option("ENABLE_HIP", True))
            hip_for_radiuss_projects(entries, spec, compiler)
        else:
            entries.append(cmake_cache_option("ENABLE_HIP", False))

        entries.append(cmake_cache_option("ENABLE_OPENMP_TARGET", "+openmp_target" in spec))
        if "+openmp_target" in spec:
            if ("%xl" in spec):
                entries.append(cmake_cache_string("BLT_OPENMP_COMPILE_FLAGS", "-qoffload;-qsmp=omp;-qnoeh;-qalias=noansi"))
                entries.append(cmake_cache_string("BLT_OPENMP_LINK_FLAGS", "-qoffload;-qsmp=omp;-qnoeh;-qalias=noansi"))
            if ("%clang" in spec):
                entries.append(cmake_cache_string("BLT_OPENMP_COMPILE_FLAGS", "-fopenmp;-fopenmp-targets=nvptx64-nvidia-cuda"))
                entries.append(cmake_cache_string("BLT_OPENMP_LINK_FLAGS", "-fopenmp;-fopenmp-targets=nvptx64-nvidia-cuda"))

        return entries

    def initconfig_package_entries(self):
        spec = self.spec
        entries = []

        option_prefix = "RAJA_" if spec.satisfies("@0.14.0:") else ""

        # TPL locations
        entries.append("#------------------{0}".format("-" * 60))
        entries.append("# TPLs")
        entries.append("#------------------{0}\n".format("-" * 60))

        entries.append(cmake_cache_path("BLT_SOURCE_DIR", spec["blt"].prefix))

        # Build options
        entries.append("#------------------{0}".format("-" * 60))
        entries.append("# Build Options")
        entries.append("#------------------{0}\n".format("-" * 60))

        entries.append(cmake_cache_string(
            "CMAKE_BUILD_TYPE", spec.variants["build_type"].value))

        entries.append(cmake_cache_string("RAJA_RANGE_ALIGN", "4"))
        entries.append(cmake_cache_string("RAJA_RANGE_MIN_LENGTH", "32"))
        entries.append(cmake_cache_string("RAJA_DATA_ALIGN", "64"))

        entries.append(cmake_cache_option("RAJA_HOST_CONFIG_LOADED", True))

        entries.append(cmake_cache_option("BUILD_SHARED_LIBS","+shared" in spec))
        entries.append(cmake_cache_option("ENABLE_OPENMP","+openmp" in spec))

        entries.append(cmake_cache_option("ENABLE_BENCHMARKS", "tests=benchmarks" in spec))
        entries.append(cmake_cache_option("ENABLE_TESTS", not "tests=none" in spec or self.run_tests))

        entries.append(cmake_cache_option("RAJA_PERFSUITE_USE_CALIPER","+caliper" in spec))
        if "+caliper" in self.spec:
            entries.append(cmake_cache_path("caliper_DIR", spec["caliper"].prefix+"/share/cmake/caliper/"))
            entries.append(cmake_cache_path("adiak_DIR", spec["adiak"].prefix+"/lib/cmake/adiak/"))

        return entries

    def cmake_args(self):
        options = [f"-DMPI_CXX_LINK_FLAGS='{self.spec['mpi'].libs.ld_flags}'"]
        return options
