# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import sys
compilers = ["gcc12","gccSpack"]
progOpts = ["O2"]
n_ranks = ["4","8","12","16","20","24","28","32"]
scaling = ["weak"]



f = open("daneRun.sh", "w")
f.write("#!/bin/bash\n#SBATCH -n 32\n#SBATCH -N 1\n#SBATCH --time 599")
for i in range(1,5):
    for progOpt in progOpts:
        for n_rank in n_ranks:
            for scale in scaling:
                for compiler in compilers:
                    filePath="./workspace/"
                    system_hash=""
                    if(compiler=="gcc12"):
                        system_hash="Rubyexp-957b932"
                    else:
                        system_hash="Rubyexp-fd15164"
                    secPath="quicksilver"+compiler+"O2weak"+str(i)+"/"+system_hash+"/workspace/experiments/quicksilver/quicksilver/quicksilver_weak"+str(n_rank)+"/execute_experiment"
                    
                    filePath+=secPath
                    print(filePath)
                    origFile= open(filePath,"r")
                    for line in origFile.readlines():
                        line=str(line)
                        if "#" not in line:
                            f.write(line)
                    origFile.close()
f.close()
