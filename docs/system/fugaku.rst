.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

==============================
Running benchpark on Fugaku
==============================

Git is needed to clone Benchpark, and Python 3.8+ is needed to run Benchpark:

.. code:: bash

    git clone https://github.com/LLNL/benchpark.git
    cd benchpark


Get in interactive shell

.. code:: bash

    pjsub --interact ...


Load newer python environment and install dependencies:

.. code:: bash

    if [ -f ~/spack/share/spack/setup-env.sh ]; then
        source ~/spack/share/spack/setup-env.sh
    else
        source /vol0004/apps/oss/spack/share/spack/setup-env.sh
    fi
    spack load python@3.10.8 /mzi2ihx; spack load py-pip@23.1.2 /4hkqlma
    pip install -r requirements.txt


Set up the directory structure for your experiment:

.. code:: bash

    export BM='saxpy/openmp'
    export SYS='RCCS-Fugaku-Fujitsu-A64FX-TofuD'
    ./bin/benchpark setup ${BM} ${SYS} workspace


Patch some files in various repos:

.. code:: bash

    sed -i -e "s@256000000@134217728@g" experiments/stream/openmp/ramble.yaml
    wget https://raw.githubusercontent.com/jdomke/spack/RIKEN_CCS_fugaku5/lib/spack/spack/util/libc.py -O workspace/spack/lib/spack/spack/util/libc.py
    wget https://raw.githubusercontent.com/jdomke/spack/RIKEN_CCS_fugaku10/var/spack/repos/builtin/packages/hpl/package.py -O workspace/spack/var/spack/repos/builtin/packages/hpl/package.py
    wget https://raw.githubusercontent.com/jdomke/spack/RIKEN_CCS_fugaku11/var/spack/repos/builtin/packages/fujitsu-ssl2/package.py -O workspace/spack/var/spack/repos/builtin/packages/fujitsu-ssl2/package.py
    #ONLY FOR CLANG BUILDS: sed -i -e 's@SYSTEM_PATHS = \[\(.*\)\]@SYSTEM_PATHS = [\1, "/opt/FJSVxtclanga/tcsds-mpi-1.2.38", "/opt/FJSVxtclanga/tcsds-ssl2-1.2.38"]@g' workspace/spack/lib/spack/spack/util/environment.py
    #ONLY FOR CLANG BUILDS: sed -i -e 's@%fj"):@%fj") or (spec.target == "a64fx" and spec.satisfies("%clang\@11:")):@g' workspace/spack/var/spack/repos/builtin/packages/cmake/package.py


Build the benchmark:

.. code:: bash

    source ./workspace/setup.sh
    export TMP=/local
    export TMPDIR=/local
    ramble --disable-progress-bar --workspace-dir $(readlink -f $(pwd)/workspace/${BM}/${SYS}/workspace) workspace setup


Go back to login node and submit benchmarks:

.. code:: bash

    if [ -f ~/spack/share/spack/setup-env.sh ]; then
        source ~/spack/share/spack/setup-env.sh
    else
        source /vol0004/apps/oss/spack/share/spack/setup-env.sh
    fi
    spack load python@3.11.6 /yjlixq5; spack load py-pip@23.1.2 /sa5bbab
    pip install -r requirements.txt
    export BM='saxpy/openmp'
    export SYS='RCCS-Fugaku-Fujitsu-A64FX-TofuD'
    ./workspace/ramble/bin/ramble --disable-progress-bar --workspace-dir $(readlink -f $(pwd)/workspace/${BM}/${SYS}/workspace) on

Finding the benchmark output (Fujitsu MPI does not write to STDOUT):

.. code:: bash

   find workspace/${BM}/${SYS}/workspace -name 'output.*'

