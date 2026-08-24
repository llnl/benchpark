..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

###################
 Experiment Status
###################

These steps reproduce CI metadata collection for the ``amg2023`` experiment on Tioga.

*************************
 Prepare the Environment
*************************

1. Log in to Tioga.
2. Clone Benchpark and enter the repository:

   ::

       git clone https://github.com/LLNL/benchpark.git
       cd benchpark

3. Create and activate a Python virtual environment:

   ::

       python3 -m venv env
       . env/bin/activate
       pip install -r requirements.txt

******************
 Collect Metadata
******************

Run the following commands to collect metadata with ROCm 6.4.2:

::

    ./bin/benchpark system init --dest=tioga_rocm_6.4.2 llnl-elcapitan cluster=tioga rocm=6.4.2
    ./bin/benchpark experiment init --dest=amg2023 tioga_rocm_6.4.2 amg2023 +rocm caliper=time,mpi
    ./bin/benchpark setup tioga_rocm_6.4.2/amg2023 wkp/
    . wkp/setup.sh
    cd ./wkp/tioga_rocm_6.4.2/amg2023/workspace/
    ramble --workspace-dir . workspace setup
    ramble --workspace-dir . on

Return to the Benchpark repository root, then repeat the workflow with ROCm 7.2.0:

::

    cd ../../../..
    ./bin/benchpark system init --dest=tioga_rocm_7.2.0 llnl-elcapitan cluster=tioga rocm=7.2.0
    ./bin/benchpark experiment init --dest=amg2023 tioga_rocm_7.2.0 amg2023 +rocm caliper=time,mpi
    ./bin/benchpark setup tioga_rocm_7.2.0/amg2023 wkp/
    . wkp/setup.sh
    cd ./wkp/tioga_rocm_7.2.0/amg2023/workspace/
    ramble --workspace-dir . workspace setup
    ramble --workspace-dir . on

******************
 Inspect Metadata
******************

After both runs complete, return to the Benchpark repository root:

::

    cd ../../../..

Compare the two locally generated metadata files:

::

    . .gitlab/utils/compare-githash-metadata.sh \
        wkp/tioga_rocm_6.4.2/amg2023/workspace/experiments/amg2023/problem1/amg2023_problem1_test_mpi_rocm_no_scaling_caliper_time_mpi_80_80_40_2_2_1_4/githash_metadata.json \
        wkp/tioga_rocm_7.2.0/amg2023/workspace/experiments/amg2023/problem1/amg2023_problem1_test_mpi_rocm_no_scaling_caliper_time_mpi_80_80_40_2_2_1_4/githash_metadata.json
