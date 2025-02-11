# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from spack.package import *
from spack.pkg.builtin.mfem import Mfem as BuiltinMfem


class Mfem(BuiltinMfem):
    # variant("rocm", default=False, description="Enable ROCm support")
    # depends_on("rocblas", when="+rocm")
    # depends_on("rocsolver", when="+rocm")

    requires("+rocm", when="^rocblas")
    requires("+rocm", when="^rocsolver")
    requires("+caliper", when="^hypre+caliper")
    requires("+mpi", when="^hypre+mpi")

    depends_on("hiprand", when="+rocm")
    depends_on("hipsparse", when="+rocm")

    version("4.4_comm_cali", branch="comm_cali", submodules=False, git="https://github.com/gracenansamba/mfem.git")

    variant("caliper", default=False, description="Build Caliper support")

    depends_on("caliper", when="+caliper")
    depends_on("adiak", when="+caliper")

    compiler_to_cpe_name = {
        "cce": "cray",
        "gcc": "gnu",
    }

    #def get_make_config_options(self, spec, prefix):
    #    def yes_no(varstr):
    #        return "YES" if varstr in self.spec else "NO"
    #    options = super(Mfem, self).get_make_config_options(spec, prefix)
    #    caliper_opt = ["MFEM_USE_CALIPER=%s" % yes_no("+caliper"), ]
    #    return options + caliper_opt



    
    #cal_dir=spec["caliper"].prefix
    #targets.append("CALIPER_DIR=%s" % spec["caliper"].prefix)
    #targets.append("ADIAK_DIR=%s" % spec["adiak"].prefix)
    def get_make_config_options(self, spec, prefix):
        def yes_no(varstr):
            return "YES" if varstr in self.spec else "NO"
        options = super(Mfem, self).get_make_config_options(spec, prefix)
        options.append("MFEM_USE_CALIPER=%s" % yes_no("+caliper"))
        if "+caliper" in self.spec: 
            options.append("CALIPER_DIR=%s" % self.spec["caliper"].prefix)
            options.append("MFEM_USE_ADIAK=%s" % yes_no("+adiak"))
            options.append("ADIAK_DIR=%s" % self.spec["adiak"].prefix)

        return options

