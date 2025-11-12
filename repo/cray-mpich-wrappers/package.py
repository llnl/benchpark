# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from spack.package import *
import os.path
import os
import stat
from spack_repo.builtin.packages.mpich.package import MpichEnvironmentModifications

class CrayMpichWrappers(MpichEnvironmentModifications, BundlePackage):

    version("1.0.0")

    depends_on("cray-mpich")
    provides("mpi")

    @property
    def libs(self):
        return self.spec["cray-mpich"].libs

    def setup_run_environment(self, env: EnvironmentModifications) -> None:
        self.setup_mpi_wrapper_variables(env)

    def setup_dependent_package(self, module, dependent_spec):
        MpichEnvironmentModifications.setup_dependent_package(self, module, dependent_spec)

    def install(self, spec, prefix):
        dep = spec["cray-mpich"]
        for subdir in os.listdir(dep.prefix):
            if subdir == "bin":
                continue
            os.symlink(os.path.join(dep.prefix, subdir), os.path.join(self.prefix, subdir))

        mkdir(self.prefix.bin)
        for target in os.listdir(dep.prefix.bin):
            if target in ["mpicc", "mpicxx", "mpif90", "mpif77"]:
                fpath = os.path.join(self.prefix.bin, target)
                with open(fpath, "w") as f:
                    f.write(f"""\
#!/bin/bash

{dep.prefix.bin}/{target} -lmpi_gtl_hsa "$@"
""")
                st = os.stat(fpath)
                os.chmod(fpath, st.st_mode | stat.S_IEXEC)
