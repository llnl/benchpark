import os

from spack.package import *
from spack.build_systems.python import PythonPackage


class PyScaffold(PythonPackage, CudaPackage, ROCmPackage):
    """Scale-Free Fractal benchmark"""

    git = "file:///usr/workspace/mckinsey/ScaFFold-spack"

    version("main", branch="spack-install")

    maintainers("michaelmckinsey")
    license("Apache-2.0")

    variant("mpi", default=True, description="MPI support")
    variant("caliper", default=False, description="Build with Caliper support enabled.")

    # TODO: Required because of how we set paths in application.py hardcoded to python3.11
    depends_on("python@3.11", type=("build", "run"))
    depends_on("py-setuptools", type="build")
    depends_on("py-wheel", type="build")
    depends_on("py-pip", type=("build", "run"))

    # depends_on("py-matplotlib", type=("build", "run"))
    # depends_on("py-numpy@1.24.3", type=("build", "run"))
    # depends_on("py-numba", type=("build", "run"))
    # depends_on("py-tqdm", type=("build", "run"))
    #depends_on("py-wandb", type=("build", "run"))
    # depends_on("py-pyyaml", type=("build", "run"))
    # depends_on("py-mpi4py", type=("build", "run"))

    depends_on("mpi")

    # depends_on("open3d+python", type=("build", "run"))

    # TODO glew wont build (dependency of open3d)
    # depends_on("glew@2.1.0", type="build")

    # These dont exist
    #depends_on("py-pyntcloud", type=("build","run"))

    depends_on("caliper+python", when="+caliper", type=("build", "run"))

    def cmake_args(self):
        args = super().cmake_args(self)

        args.append(self.define("CMAKE_EXE_LINKER_FLAGS", self.spec['mpi'].libs.ld_flags))
        args.append(self.define("MPI_CXX_LINK_FLAGS", self.spec['mpi'].libs.ld_flags))

        return args

    def setup_build_environment(self, env):
        super().setup_build_environment(env)

        if self.compiler.extra_rpaths:
            for rpath in self.compiler.extra_rpaths:
                env.prepend_path("LD_LIBRARY_PATH", rpath)

        if "+mpi" in self.spec:
            if self.spec["mpi"].extra_attributes:
                if "ldflags" in self.spec["mpi"].extra_attributes:
                    env.append_flags("LDFLAGS", self.spec["mpi"].extra_attributes["ldflags"])
                if "gtl_lib_path" in self.spec["mpi"].extra_attributes:
                    env.prepend_path("LD_LIBRARY_PATH", self.spec['mpi'].extra_attributes["gtl_lib_path"])

    def setup_run_environment(self, env):
        super().setup_run_environment(env)


        if "+mpi" in self.spec:
            if self.spec["mpi"].extra_attributes:
                if "gtl_lib_path" in self.spec["mpi"].extra_attributes:
                    env.prepend_path("LD_LIBRARY_PATH", self.spec['mpi'].extra_attributes["gtl_lib_path"])

        # if self.spec.satisfies("+caliper"):
        #     # Avoid libcaffe2_nvrtc.so
        #     env.prepend_path("LD_LIBRARY_PATH", os.path.join(self.spec.prefix.join(python_platlib), "torch", "lib"))
        #     if self.spec.satisfies("+cuda"):
        #         # Avoid libcudnn_graph.so error (unecessary if cuX_full, necessary if cuX wheel)
        #         env.prepend_path("LD_LIBRARY_PATH", os.path.join(self.spec.prefix.join(python_platlib), "nvidia", "cudnn", "lib"))

        # print(prefix)
        # print(python_platlib)
        # print(self.spec["caliper"].prefix)
        if self.spec.satisfies("+caliper"):
            if self.spec.satisfies("+rocm"):
                env.set("ROCP_TOOL_LIBRARIES", os.path.join(self.spec["caliper"].prefix, "lib64", "libcaliper.so"))

        if self.compiler.extra_rpaths:
            for rpath in self.compiler.extra_rpaths:
                env.prepend_path("LD_LIBRARY_PATH", rpath)
