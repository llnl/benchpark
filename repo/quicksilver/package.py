# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from spack.package import *


class Quicksilver(MakefilePackage):
    """Quicksilver is a proxy application that represents some elements of the
    Mercury workload.
    """

    tags = ["proxy-app"]

    homepage = "https://codesign.llnl.gov/quicksilver.php"
    url = "https://github.com/LLNL/Quicksilver/tarball/V1.0"
    git = "https://github.com/august-knox/Quicksilver.git"

    maintainers("richards12")

    version("caliper", branch="feature/caliper-annotations")
    version("master", branch="master")
    version("1.0", sha256="83371603b169ec75e41fb358881b7bd498e83597cd251ff9e5c35769ef22c59a")

    variant("openmp", default=False, description="Build with OpenMP support")
    variant("mpi", default=False, description="Build with MPI support")
    variant("cuda", default=False, description="Build with CUDA support")
    variant("caliper", default=False, description="Build with Caliper support")

    depends_on("c", type="build")

    depends_on("mpi", when="+mpi")
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")

    build_directory = "src"

    @property
    def build_targets(self):
        targets = []
        spec = self.spec
        
        if "+caliper" in spec: 
            targets.append("CALIPER_DIR=%s" % spec["caliper"].prefix)
            targets.append("ADIAK_DIR=%s" % spec["adiak"].prefix)

        if "+cuda" in spec:
            targets.append("CXXFLAGS= -DHAVE_CUDA {0}".format(self.compiler.cxx11_flag))
        else:
            targets.append("CXXFLAGS={0}".format(self.compiler.cxx11_flag))

        if "+mpi" in spec:
            targets.append("CXX={0}".format(spec["mpi"].mpicxx))
        else:
            targets.append("CXX={0}".format(spack_cxx))

        caliper_flag = "-DUSE_CALIPER -DUSE_ADIAK" 

        if "+openmp+mpi" in spec:
            targets.append("CPPFLAGS=-DHAVE_MPI -DHAVE_OPENMP {0} {1}".format(caliper_flag, self.compiler.openmp_flag))
        elif "+openmp" in spec:
            targets.append("CPPFLAGS=-DHAVE_OPENMP {0} {1}".format(caliper_flag, self.compiler.openmp_flag))
        elif "+mpi" in spec:
            targets.append("CPPFLAGS=-DHAVE_MPI {0}".format(caliper_flag))
        if "+openmp" in self.spec:
            if "~caliper" in self.spec:
                targets.append("LDFLAGS={0}".format(self.compiler.openmp_flag))

        return targets

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        mkdir(prefix.doc)
        install("src/qs", prefix.bin)
        install("LICENSE.md", prefix.doc)
        install("README.md", prefix.doc)
        install_tree("Examples", prefix.Examples)
