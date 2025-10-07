import os

from spack.package import *
from spack.build_systems.python import PythonPackage


class PyScaffold(PythonPackage, CudaPackage, ROCmPackage):
    """Scale-Free Fractal benchmark"""

    git = "file:///usr/workspace/mckinsey/ScaFFold-spack"

    version("main", branch="spack-install")

    maintainers("michaelmckinsey")
    license("Apache-2.0")

    variant("caliper", default=False, description="Build with Caliper support enabled.")

    depends_on("python@3.11:", type=("build", "run"))
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

    def setup_run_environment(self, env):
        super().setup_run_environment(env)

        env.prepend_path("LD_LIBRARY_PATH", self.spec['mpi'].libs.gtl_lib_path)

        if self.spec.satisfies("+caliper"):
            env.prepend_path("LD_LIBRARY_PATH", os.path.join(self.spec.prefix.join(python_platlib), "torch", "lib"))

        if self.compiler.extra_rpaths:
            for rpath in self.compiler.extra_rpaths:
                env.prepend_path("LD_LIBRARY_PATH", rpath)
