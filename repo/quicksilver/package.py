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

    version("master", branch="master")
    version("1.0", sha256="83371603b169ec75e41fb358881b7bd498e83597cd251ff9e5c35769ef22c59a")
    version("caliper", branch="feature/caliper-annotations")
    variant("openmp", default=False, description="Build with OpenMP support")
    variant("mpi", default=False, description="Build with MPI support")
    variant("cuda", default=False, description="Build with CUDA support")
    variant("caliper", default=False, description="Build with Caliper support")
    depends_on("mpi", when="+mpi")
    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")

    build_directory = "src"

    @property
    def build_targets(self):
        targets = []
        spec = self.spec
        if "+cuda" in spec:
            targets.append("CXXFLAGS= -DHAVE_CUDA {0}".format(self.compiler.cxx11_flag))
        else:
            targets.append("CXXFLAGS={0}".format(self.compiler.cxx11_flag))

        if "+caliper" in spec: 
            cal_dir=spec["caliper"].prefix
            targets.append("CALIPER_DIR=%s" % spec["caliper"].prefix)
            targets.append("ADIAK_DIR=%s" % spec["adiak"].prefix)
            #print($CALIPER_DIR
            #targets.append("CALIPER_FLAGS = -I "+cal_dir+"/include -DUSE_CALIPER")
            #targets.append("CALIPER_LDFLAGS = -L "+cal_dir+"/lib64 -lcaliper")
        if "+mpi" in spec:
            targets.append("CXX={0}".format(spec["mpi"].mpicxx))
        else:
            targets.append("CXX={0}".format(spack_cxx))

        if "+openmp+mpi" in spec:
            targets.append("CPPFLAGS=-DHAVE_MPI -DHAVE_OPENMP -DUSE_CALIPER -DUSE_ADIAK {0}".format(self.compiler.openmp_flag))
        elif "+openmp" in spec:
            targets.append("CPPFLAGS=-DHAVE_OPENMP -DUSE_CALIPER {0}".format(self.compiler.openmp_flag))
        elif "+mpi" in spec:
            targets.append("CPPFLAGS=-DHAVE_MPI -DUSE_CALIPER {0}")
        #if "+openmp" in spec:
            #targets.append("LDFLAGS={0}".format(self.compiler.openmp_flag))
        return targets

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        mkdir(prefix.doc)
        install("src/qs", prefix.bin)
        install("LICENSE.md", prefix.doc)
        install("README.md", prefix.doc)
        install_tree("Examples", prefix.Examples)
