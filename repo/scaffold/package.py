# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack import *


class Scaffold(ROCmPackage, PythonExtension):

    git = "https://github.com/LBANN/ScaFFold"

    version("develop", branch="main")

    # depends_on("rocm@6.2.1")
    # depends_on("rocmcc@6.2.1-cce-18.0.1a-magic")
    # depends_on("python@3.9.12")

    @run_after("install")
    def install_python(self):
        # do LAMMPS Python package installation using pip
        # if self.spec.satisfies("@20230328: +python"):
        # with working_dir("python"):
        #     os.environ["LAMMPS_VERSION_FILE"] = join_path(
        #         self.stage.source_path, "src", "version.h"
        #     )
        pip(*PythonPipBuilder.std_args(self), f"--prefix={self.prefix}", ".")
