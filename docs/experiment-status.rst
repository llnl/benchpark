..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

###################
 Experiment Status
###################

These steps reproduce CI metadata collection for the ``py-scaffold`` experiment on
Tuolumne.

*************************
 Prepare the Environment
*************************

1. Log in to Tuolumne.
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

    ./bin/benchpark system init --dest=tuolumne_642 llnl-elcapitan cluster=tuolumne rocm=6.4.2
    ./bin/benchpark experiment init --dest=py-scaffold tuolumne_642 py-scaffold +rocm package_manager=spack-pip caliper=time,rocm,rocm-gputime,rccl allocation=torchrun-hpc
    ./bin/benchpark setup tuolumne_642/py-scaffold wkp/
    . wkp/setup.sh
    cd ./wkp/tuolumne_642/py-scaffold/workspace/
    ramble --workspace-dir . workspace setup
    ramble --workspace-dir . on

Return to the Benchpark repository root, then repeat the workflow with ROCm 7.2.0:

::

    cd ../../../..
    ./bin/benchpark system init --dest=tuolumne_720 llnl-elcapitan cluster=tuolumne rocm=7.2.0
    ./bin/benchpark experiment init --dest=py-scaffold tuolumne_720 py-scaffold +rocm package_manager=spack-pip caliper=time,rocm,rocm-gputime,rccl allocation=torchrun-hpc
    ./bin/benchpark setup tuolumne_720/py-scaffold wkp/
    . wkp/setup.sh
    cd ./wkp/tuolumne_720/py-scaffold/workspace/
    ramble --workspace-dir . workspace setup
    ramble --workspace-dir . on

******************
 Compare Metadata
******************

After both runs complete, return to the Benchpark repository root and define the
experiment directories:

::

    cd ../../../..
    rocm_642_experiment=wkp/tuolumne_642/py-scaffold/workspace/experiments/py_scaffold/sweep/py_scaffold_sweep_test_rocm_no_scaling_caliper_time_rocm_rocm_gputime_rccl_4_6_10_1
    rocm_720_experiment=wkp/tuolumne_720/py-scaffold/workspace/experiments/py_scaffold/sweep/py_scaffold_sweep_test_rocm_no_scaling_caliper_time_rocm_rocm_gputime_rccl_4_6_10_1

Verify that each experiment directory contains a ``githash_metadata.json`` file:

::

    test -f "${rocm_642_experiment}/githash_metadata.json"
    test -f "${rocm_720_experiment}/githash_metadata.json"

Compare the two metadata files:

::

    .gitlab/utils/compare-githash-metadata.sh \
        "${rocm_642_experiment}" \
        "${rocm_720_experiment}"

The comparison script generates a JSON file describing the differences between the two
metadata files.
