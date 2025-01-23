# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *

# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Enzyme(CMakePackage):
    """
    The Enzyme project is a tool for performing reverse-mode automatic
    differentiation (AD) of statically-analyzable LLVM IR.
    This allows developers to use Enzyme to automatically create gradients
    of their source code without much additional work.
    """

    homepage = "https://enzyme.mit.edu"
    git = "https://github.com/EnzymeAD/Enzyme.git"

    maintainers("wsmoses", "jandrej")

    root_cmakelists_dir = "enzyme"

    version("main", branch="main")
    version("0.0.165", sha256="c87b3ad80ebdc6503966d7187a008ed7c84a7e4c")

    depends_on("c", type="build")  # generated
    depends_on("cxx", type="build")  # generated
    depends_on("fortran", type="build")  # generated

    depends_on("llvm@7:12", when="@0.0.13:0.0.15")
    depends_on("llvm@7:14", when="@0.0.32:0.0.47")
    depends_on("llvm@7:14", when="@0.0.48:0.0.68")
    depends_on("llvm@9:16", when="@0.0.69:0.0.79")
    depends_on("llvm@11:16", when="@0.0.80:0.0.99")
    depends_on("llvm@11:19", when="@0.0.100:")
    depends_on("cmake@3.13:", type="build")

    def cmake_args(self):
        spec = self.spec
        args = ["-DLLVM_DIR=" + spec["llvm"].prefix.lib + "/cmake/llvm"]
        return args

    @property
    def libs(self):
        ver = self.spec["llvm"].version.up_to(1)
        libs = ["LLVMEnzyme-{0}".format(ver), "ClangEnzyme-{0}".format(ver)]
        if self.version >= Version("0.0.32"):  # TODO actual lower bound
            libs.append("LLDEnzyme-{0}".format(ver))

        return find_libraries(libs, root=self.prefix, recursive=True)

    def setup_dependent_build_environment(self, env, dependent_spec):
        # Get the LLVMEnzyme and ClangEnzyme lib paths
        llvm, clang = self.libs

        if "LLVMEnzyme-" in clang:
            llvm, clang = clang, llvm

        env.set("LLVMENZYME", llvm)
        env.set("CLANGENZYME", clang)
