..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#############################
 Running benchpark on Fugaku
#############################

Git is needed to clone Benchpark, and Python 3.8+ is needed to run Benchpark:

.. code-block:: bash

    git clone https://github.com/LLNL/benchpark.git
    cd benchpark

Get in interactive shell

.. code-block:: bash

    pjsub --interact ...

Load newer python environment and install dependencies:

.. code-block:: bash

    if [ -f ~/spack/share/spack/setup-env.sh ]; then
        source ~/spack/share/spack/setup-env.sh
    else
        source /vol0004/apps/oss/spack/share/spack/setup-env.sh
    fi
    spack load python@3.10.8 /mzi2ihx; spack load py-pip@23.1.2 /ojmntoi
    pip install -r requirements.txt

Set up the directory structure for your experiment:

.. code-block:: bash

    . setup-env.sh
    export BM="saxpy"
    export SYS="fugaku"
    export WSDIR="$(pwd)/workspace"
    benchpark system init --dest=${SYS}-system ${SYS}
    benchpark experiment init --dest=${BM}-test ${SYS}-system ${BM} +openmp
    benchpark setup ./${SYS}-system/${BM}-test ${WSDIR}

Patch some files in various repos:

.. code-block:: bash

    #sed -i -e "s@256000000@134217728@g" experiments/stream/openmp/ramble.yaml
    #wget https://raw.githubusercontent.com/jdomke/spack/RIKEN_CCS_fugaku5/lib/spack/spack/util/libc.py -O ${WSDIR}/spack/lib/spack/spack/util/libc.py
    wget https://raw.githubusercontent.com/jdomke/spack/RIKEN_CCS_fugaku10/var/spack/repos/builtin/packages/hpl/package.py -O ${WSDIR}/spack-packages/repos/spack_repo/builtin/packages/hpl/package.py
    wget https://raw.githubusercontent.com/SBA0486/spack-packages/refs/heads/develop/repos/spack_repo/builtin/packages/fujitsu_ssl2/package.py -O ${WSDIR}/spack-packages/repos/spack_repo/builtin/packages/fujitsu_ssl2/package.py
    wget https://raw.githubusercontent.com/SBA0486/spack-packages/refs/heads/develop/repos/spack_repo/builtin/packages/fujitsu_mpi/package.py -O ${WSDIR}/spack-packages/repos/spack_repo/builtin/packages/fujitsu_mpi/package.py
    sed -i -e 's@SYSTEM_PATHS = \[\(.*\)\]@SYSTEM_PATHS = [\1, "/opt/FJSVxtclanga/tcsds-mpi-1.2.38", "/opt/FJSVxtclanga/tcsds-ssl2-1.2.38"]@g'  ${WSDIR}/spack/lib/spack/spack/util/environment.py
    sed -i -e 's@%fj"):@%fj") or (spec.target == "a64fx" and spec.satisfies("%clang\@11:")):@g'  ${WSDIR}/spack-packages/repos/spack_repo/builtin/packages/cmake/package.py

Build the benchmark:

.. code-block:: bash

    source ${WSDIR}/setup.sh
    export TMP=/local
    export TMPDIR=/local
    ramble --workspace-dir ${WSDIR}/${BM}-test/${SYS}-system/workspace workspace setup

Go back to login node and submit benchmarks:

.. code-block:: bash

    if [ -f ~/spack/share/spack/setup-env.sh ]; then
        source ~/spack/share/spack/setup-env.sh
    else
        source /vol0004/apps/oss/spack/share/spack/setup-env.sh
    fi
    spack load python@3.11.6 /yjlixq5; spack load py-pip@23.1.2 /sa5bbab
    pip install -r requirements.txt
    export BM="saxpy"
    export SYS="fugaku"
    export WSDIR="$(pwd)/workspace"
    ${WSDIR}/ramble/bin/ramble --workspace-dir ${WSDIR}/${BM}-test/${SYS}-system/workspace on

Finding the benchmark output (Fujitsu MPI does not write to STDOUT):

.. code-block:: bash

    find ${WSDIR}/${BM}-test/${SYS}-system/workspace/experiments/${BM}/ -name '*.out'
    #find ${WSDIR}/${BM}-test/${SYS}-system/workspace/experiments/${BM}/ -name 'fjmpioutdir'
    #find ${WSDIR}/${BM}-test/${SYS}-system/workspace/experiments/${BM}/ -name 'output.*'
