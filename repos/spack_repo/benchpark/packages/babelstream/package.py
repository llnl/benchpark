# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *


class Babelstream(BuiltinBabel):

    git = "https://github.com/august-knox/BabelStream.git"
    version("5.0", tag="v5.0")
    version("4.0", sha256="a9cd39277fb15d977d468435eb9b894f79f468233f0131509aa540ffda4f5953")
    version("main", branch="main")
    version("develop", branch="develop")
    version("caliper", branch="caliper-annotations")

    maintainers("tomdeakin", "kaanolgu", "tom91136", "robj0nes")

    # Languages
    # Also supported variants are cuda and rocm (for HIP)
    variant("sycl", default=False, description="Enable SYCL support")
    variant("sycl2020", default=False, description="Enable SYCL support")
    variant("openmp", default=False, description="Enable OpenMP support")
    variant("ocl", default=False, description="Enable OpenCL support")
    variant("tbb", default=False, description="Enable TBB support")
    variant("acc", default=False, description="Enable OpenACC support")
    variant("thrust", default=False, description="Enable THRUST support")
    variant("raja", default=False, description="Enable RAJA support")
    variant("stddata", default=False, description="Enable STD-data support")
    variant("stdindices", default=False, description="Enable STD-indices support")
    variant("stdranges", default=False, description="Enable STD-ranges support")
    variant("caliper", default=False, description="Enable caliper annotations")
    # Some models need to have the programming model abstraction downloaded -
    # this variant enables a path to be provided.
    variant("dir", values=str, default="none", description="Enable Directory support")

    # Kokkos conflict and variant
    conflicts(
        "dir=none", when="+kokkos", msg="KOKKKOS requires architecture to be specified by dir="
    )
    variant("kokkos", default=False, description="Enable KOKKOS support")

    # ACC conflict
    variant("cpu_arch", values=str, default="none", description="Enable CPU Target for ACC")
    variant("backend", values=str, default="none", description="Enable CPU Target for ACC")

    # STD conflicts
    conflicts("+stddata", when="%gcc@:10.1.0", msg="STD-data requires newer version of GCC")
    conflicts("+stdindices", when="%gcc@:10.1.0", msg="STD-indices requires newer version of GCC")
    conflicts("+stdranges", when="%gcc@:10.1.0", msg="STD-ranges requires newer version of GCC")

    # CUDA conflict
    conflicts(
        "cuda_arch=none",
        when="+cuda",
        msg="CUDA requires architecture to be specified by cuda_arch=",
    )
    variant("mem", values=str, default="DEFAULT", description="Enable MEM Target for CUDA")
    # Raja Conflict
    variant(
        "offload", values=str, default="none", description="Enable RAJA Target [CPU or NVIDIA]"
    )
    conflicts(
        "offload=none",
        when="+raja",
        msg="RAJA requires architecture to be specified by backend=[CPU,NVIDIA]",
    )

    # download raja from https://github.com/LLNL/RAJA
    conflicts(
        "dir=none",
        when="+raja",
        msg="RAJA implementation requires architecture to be specified by dir=",
    )

    # Confirmed c++ and Fortran
    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    # Thrust Conflict
    # conflicts("~cuda", when="+thrust", msg="Thrust requires +cuda variant")
    depends_on("thrust", when="+thrust")
    depends_on("rocthrust", when="+thrust implementation=rocm")

    # TBB Dependency
    depends_on("intel-oneapi-tbb", when="+tbb")
    partitioner_vals = ["auto", "affinity", "static", "simple"]
    variant(
        "partitioner",
        values=partitioner_vals,
        default="auto",
        description="Partitioner specifies how a loop template should partition its work among threads.\
            Possible values are:\
            AUTO     - Optimize range subdivision based on work-stealing events.\
            AFFINITY - Proportional splitting that optimizes for cache affinity.\
            STATIC   - Distribute work uniformly with no additional load balancing.\
            SIMPLE   - Recursively split its range until it cannot be further subdivided.\
            See https://spec.oneapi.com/versions/latest/elements/oneTBB/source/algorithms.html#partitioners for more details.",
    )

    # Kokkos Dependency
    depends_on("kokkos@3.7.1", when="+kokkos")

    #caliper dependency
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")

    requires("+omp", when="+openmp")
    requires("~omp", when="~openmp")

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    
class CMakeBuilder(BuiltinBuilder):
    def cmake_args(self):
        args = super().cmake_args()
        #enable caliper
        if "+caliper" in self.spec:
            args.append(self.define_from_variant("ENABLE_CALIPER", "caliper"))
        return args

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")

    def setup_run_environment(self, env):
        super().setup_run_environment(env)
        if "+cuda" in self.spec:
            env.set("NVCC_APPEND_FLAGS", "-allow-unsupported-compiler")
