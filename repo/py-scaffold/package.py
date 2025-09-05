from spack.package import *
from spack.build_systems.python import PythonPackage


class PyScaffold(PythonPackage, CudaPackage, ROCmPackage):
    """Scale-Free Fractal benchmark"""

    git = "file:///usr/workspace/mckinsey/ScaFFold-spack"

    version("main", branch="main")

    homepage = "https://<project-homepage-or-readme>"
    maintainers("michaelmckinsey")
    license("BSD-3-Clause")

    variant("caliper", default=False, description="Build with Caliper support enabled.")

    depends_on("python@3.11:", type=("build", "run"))
    depends_on("py-setuptools", type="build")
    depends_on("py-wheel", type="build")

    depends_on("py-matplotlib", type=("build", "run"))
    depends_on("py-numpy", type=("build", "run"))
    depends_on("py-numba@0.60.0", type=("build", "run"))
    depends_on("py-tqdm", type=("build", "run"))
    depends_on("py-wandb", type=("build", "run"))
    depends_on("py-pyyaml", type=("build", "run"))
    depends_on("py-mpi4py", type=("build", "run"))

    #depends_on("open3d+python", type="build")

    depends_on("caliper+python", when="+caliper")

    # These dont exist
    #depends_on("py-pyntcloud", type=("build","run"))