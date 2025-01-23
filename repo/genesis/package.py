# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class Genesis(AutotoolsPackage):
    """GENESIS package contains two MD programs (atdyn and spdyn), trajectory
    analysis programs, and other useful tools. GENESIS (GENeralized-Ensemble
    SImulation System) has been developed mainly by Sugita group in RIKEN-CCS.
    """
    
    tags = ['genesis','benchmark']
    
    homepage = "https://www.r-ccs.riken.jp/labs/cbrt/"
    git = "https://github.com/genesis-release-r-ccs/genesis"

    version("main", branch="main", submodules=False)
    version(
        "2.1.4", submodules=False, tag="v2.1.4", commit="48fa5654ae1ecdf606fb6cd0bdcc2952f5caaa65"
    )
    version(
        "2.1.3", submodules=False, tag="v2.1.3", commit="835ef1538f9350cfa7e9489f340837d0908afbd2"
    )
    version(
        "2.1.1", submodules=False, tag="v2.1.1", commit="38a54fe1c749f4d87bff591e65c61b23a7396f9d"
    )
    version(
        "2.0.3", submodules=False, tag="v2.0.3", commit="6989e0b24470e374ea343b2b7b685aca87909571"
    )

    variant("mpi", default=True, description="Build with MPI.")
    variant("openmp", default=True, description="Build with OpenMP enabled.")
    variant("lapack", default=True, description="Build with LAPACK enabled.")
    variant("gpu", default=False, description="Build with GPGPU enabled.")
    variant("precision", description="Build with selected precision.", default="double", values=("double", "mixed", "single", "large_int"), multi=False)
    variant("simd", description="Build with SIMD width.", default="auto", values=("auto", "MIC-AVX512", "CORE-AVX512", "CORE-AVX2"), multi=False)
    variant("debug", description="Set Debug level", default="0", values=("0", "1", "2", "3", "4"), multi=False)

    depends_on("mpi", when="+mpi")
    depends_on("lapack", when="+lapack")
    depends_on("cuda", when="+gpu")

    def autoreconf(self, spec, prefix):
        bash = which("bash")
        bash("./bootstrap")

    @run_before("configure")
    def fix_programming_error(self):
        spec = self.spec
        if self.version < Version("2.1.3"):
            filter_file(r"atomcls1\(1:3\)", "atomcls1(1:6)", join_path(self.stage.source_path, "src/analysis/sp_analysis/hbond_analysis/hbond_analyze.fpp"))
            filter_file(r"atomcls2\(1:3\)", "atomcls2(1:6)", join_path(self.stage.source_path, "src/analysis/sp_analysis/hbond_analysis/hbond_analyze.fpp"))

    def configure_args(self):
        spec = self.spec
        config_args = [f"--enable-{spec.variants['precision'].value}",
                       f"--with-simd={spec.variants['simd'].value}"]

        if int(spec.variants['debug'].value) > 0:
            config_args.extend(f"--enable-debug={spec.variants['debug'].value}")

        config_args.extend(self.enable_or_disable("mpi"))
        config_args.extend(self.enable_or_disable("openmp"))
        config_args.extend(self.with_or_without("lapack"))
        config_args.extend(self.enable_or_disable("gpu"))

        if "+mpi" in spec:
            env["CC"] = spec["mpi"].mpicc
            env["CXX"] = spec["mpi"].mpicxx
            env["FC"] = spec["mpi"].mpifc
            env["F77"] = spec["mpi"].mpif77

        if "+openmp" in spec and spec.satisfies("%clang"):
            env["OPT_OPENMP"] = "-fopenmp"

        if spec.satisfies("%clang"):
            opt_flags = "-Ofast -ffast-math"
            env["CFLAGS"] = f"{opt_flags}"
            env["CXXFLAGS"] = f"{opt_flags}"
            env["FCFLAGS"] = f"{opt_flags} -Mbackslash"
            env["F77FLAGS"] = f"{opt_flags} -Mbackslash"
            # cpp workaround; other systems and OS likely need different pre-processor fix
            if spec.target == "a64fx":
                env["FPP"] = "/opt/FJSVxtclanga/tcsds-1.2.38/bin/../lib/fpp"
                env["PPFLAGS"] = "-traditional-cpp -traditional"
        elif spec.satisfies("%fj"):
            opt_flags = "-Kfast"
            env["CFLAGS"] = f"{opt_flags}"
            env["CXXFLAGS"] = f"{opt_flags}"
            env["FCFLAGS"] = f"{opt_flags}"
            env["F77FLAGS"] = f"{opt_flags}"
            if spec.target == "a64fx":
                # Using same flags as the version installed outside benchpark
                env["CFLAGS"] = "-Kfast -Kocl -Kswp"
                env["FCFLAGS"] = "-Kocl -Kfast -Kopenmp -Nlst=t -Koptmsg=2"
                env["LDFLAGS"] = "-SSL2BLAMP -Kparallel -Kopenmp -Nlibomp"
                # if Lapack_libs is not specified, build fails when linking
                env["LAPACK_LIBS"] = spec["lapack"].libs.ld_flags
        elif spec.satisfies("%gcc"):
            opt_flags = "-O3 -ffast-math"
            env["CFLAGS"] = f"{opt_flags}"
            env["CXXFLAGS"] = f"{opt_flags}"
            env["FCFLAGS"] = f"{opt_flags} -ffree-line-length-none"
            env["F77FLAGS"] = f"{opt_flags} -ffree-line-length-none"

        if "+gpu" in spec:
            config_args.extend(self.with_or_without("cuda", activation_value=spec["cuda"].prefix))

        return config_args
