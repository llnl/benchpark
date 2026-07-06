# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import sys

from ramble.appkit import *


class SpartaSnl(ExecutableApplication):
    """Define SNL Sparta application"""

    name = "sparta-snl"

    maintainers("rfhaque")
    
    executable('sparta', 'spa_ -in {in} {sparta_flags}', use_mpi=True)

    executable(
        "copy",
        template=["cp {problem_dir}/* {experiment_run_dir}/"],
        use_mpi=False,
    )
    executable(
        "set-size",
        template=[
            "sed -i -e 's/xmin equal .*/xmin equal {xmin}*$\{L\}/g' -i {in}",
            "sed -i -e 's/xmax equal .*/xmax equal {xmax}*$\{L\}/g' -i {in}",
            "sed -i -e 's/ymin equal .*/ymin equal {ymin}*$\{L\}/g' -i {in}",
            "sed -i -e 's/ymax equal .*/ymax equal {ymax}*$\{L\}/g' -i {in}",
            "sed -i -e 's/ppc equal .*/ppc equal {ppc}/g' -i {in}",
            "sed -i -e 's/L equal .*/L index {L}./g' -i {in}",
            "sed -i -e 's/variable[[:space:]]\+tstep.*/# The default time step is too small\\\n"
            "# variable            tstep equal (-$\{xmin\}+$\{xmax\})\/$\{Vx\}\/$\{xncells\}\/10\/4\\\n"
            "variable            tstep equal (-$\{xmin\}+$\{xmax\})\/$\{Vx\}\/$\{xncells\}\/4/' -i {in}",
            "sed -i -e 's/circle_R0.5_P10000.surf .*/circle_R0.5_P10000.surf group 1 invert scale $\{L\} $\{L\} 1.0/g' -i {in}",
            "sed -i -e 's/collide_modify .*/collide_modify      {collide_modify}/g' -i {in}",
        ],
        use_mpi=False,
    )
    executable(
        "set-timesteps",
        template=[
            "sed -i -e 's/stats.*[0-9]\+/stats               {stats}\\\n"
            "\\\n"
            "# Some systems buffer extensively\\\n"
            "stats_modify        flush yes\\\n"
            "\\\n"
            "# Stop after 11 minutes\\\n"
            "fix 1 halt 10 tlimit > 660.0 message no\\\n"
            "\\\n"
            "# Print out the value of L for parsing ease\\\n"
            "print \"The value of L is \$L\" /' -i {in}",

            "sed 's/run.*[0-9]\+/run                 {run}/g' -i {in}",
        ],
        use_mpi=False,
    )

    workload('cylinder', executables=["copy", "set-size", "set-timesteps", "sparta"])

    workload_variable('problem_dir', default='{sparta-snl}/examples/cylinder',
            description='problem dir',
            workloads=['cylinder'])

    workload_variable('in', default='in.cylinder',
            description='input file',
            workloads=['cylinder'])

    workload_variable('L', default='1',
            description='length scale factor',
            workloads=['cylinder'])

    workload_variable('ppc', default='47',
            description='particles per cell',
            workloads=['cylinder'])
    
    workload_variable('xmin', default='-1.0',
            description='xmin',
            workloads=['cylinder'])
    
    workload_variable('xmax', default='1.1',
            description='xmax',
            workloads=['cylinder'])
    
    workload_variable('ymin', default='-1.1',
            description='ymin',
            workloads=['cylinder'])
    
    workload_variable('ymax', default='1.1',
            description='ymax',
            workloads=['cylinder'])
    
    workload_variable('collide_modify', default='vremax 100 yes vibrate no rotate smooth nearcp yes 10',
            description='collisions config',
            workloads=['cylinder'])

    workload_variable('stats', default='10',
            description='FOM interval',
            workloads=['cylinder'])

    workload_variable('run', default='100',
            description='number of intervals',
            workloads=['cylinder'])
