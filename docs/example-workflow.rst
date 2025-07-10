.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

=========================
Hello Benchpark Example
=========================


.. note::

    Make sure you can use the benchpark command; check by typing in::

        benchpark --version

    You should receive ``0.1.0`` on the terminal

Search the available benchmarks, systems, modifiers, and experiments in
Benchpark::

    benchpark list
    benchpark list experiments --experiment kripke

We will be using the Kripke experiment for this tutorial.

This tutorial will guide you through the process of using Benchpark in a
container.  In this case, the ``system``, and the ``benchmark``
and ``experiment`` are already configured and just need to be setup and run.

.. note:

    Add steps to init, setup, build, run analyze on existing system (container
    ideally)

1. Navigate into the benchpark directory::

    cd benchpark

2. Initialize the variant of the AWS system using the existing system specification in Benchpark::

    benchpark system init --dest=tutorial aws-tutorial instance_type=c7i.24xlarge

3. To run the openmp, single node scaling version of the Kripke benchmark, initialize it for experiments::

    benchpark experiment init --dest kripke-benchmark kripke scaling=strong caliper=time,mpi

4. Then setup the workspace directory for the system and experiment together::

    benchpark setup kripke-benchmark/ tutorial/ wkp/

.. note::

    This command configures a Ramble workspace using the system specification from ``benchpark system init``
    and experiment specification from ``benchpark experiment init``. Ramble can then use this workspace to
    build, run, and configure the Kripke benchmark for the AWS System we are using for this tutorial.


Benchpark will provide next steps to the console but they are also provided here. 

5. Run the setup script for dependency software, Ramble and Spack::

    . /home/jovyan/benchpark/wkp/setup.sh

6. Then setup the Ramble experiment workspace::

    ramble --disable-progress-bar --workspace-dir /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace workspace setup

This command does 2 main things. First, it builds all necessary software using Spack. This process may take some time (2-3 minutes).
Second, this command configures files (e.g. Flux submission script) needed to perform the runs that make up the current experiment.
For each run, a directory will be created under ``benchpark/wkp3/kripke_exp/tuttest/workspace/experiments/kripke/kripke``. 
If the setup is successfull, you will see something like this after the setup command::

    ==> Streaming details to log:
    ==>   /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace/logs/setup.2025-07-09_18.08.23.out
    ==>   Setting up 4 out of 4 experiments:
    ==> Experiment #1 (1/4):
    ==>     name: kripke.kripke.kripke_kripke_single_node_strong_scaling_caliper_time_mpi_2_2_1_64_64_32_64_1_128_128_4_4
    ==>     root experiment_index: 1
    ==>     log file: /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace/logs/setup.2025-07-09_18.08.23/kripke.kripke.kripke_kripke_single_node_strong_scaling_caliper_time_mpi_2_2_1_64_64_32_64_1_128_128_4_4.out
    ==>   Returning to log file: /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace/logs/setup.2025-07-09_18.08.23.out
    ==> Experiment #2 (2/4):
    ==>     name: kripke.kripke.kripke_kripke_single_node_strong_scaling_caliper_time_mpi_2_2_2_64_64_32_64_1_128_128_4_8
    ==>     root experiment_index: 2
    ==>     log file: /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace/logs/setup.2025-07-09_18.08.23/kripke.kripke.kripke_kripke_single_node_strong_scaling_caliper_time_mpi_2_2_2_64_64_32_64_1_128_128_4_8.out
    ==>   Returning to log file: /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace/logs/setup.2025-07-09_18.08.23.out
    ==> Experiment #3 (3/4):
    ==>     name: kripke.kripke.kripke_kripke_single_node_strong_scaling_caliper_time_mpi_4_2_2_64_64_32_64_1_128_128_4_16
    ==>     root experiment_index: 3
    ==>     log file: /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace/logs/setup.2025-07-09_18.08.23/kripke.kripke.kripke_kripke_single_node_strong_scaling_caliper_time_mpi_4_2_2_64_64_32_64_1_128_128_4_16.out
    ==>   Returning to log file: /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace/logs/setup.2025-07-09_18.08.23.out
    ==> Experiment #4 (4/4):
    ==>     name: kripke.kripke.kripke_kripke_single_node_strong_scaling_caliper_time_mpi_4_4_2_64_64_32_64_1_128_128_4_32
    ==>     root experiment_index: 4
    ==>     log file: /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace/logs/setup.2025-07-09_18.08.23/kripke.kripke.kripke_kripke_single_node_strong_scaling_caliper_time_mpi_4_4_2_64_64_32_64_1_128_128_4_32.out
    ==>   Returning to log file: /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace/logs/setup.2025-07-09_18.08.23.out

7. Next, we run the Kripke experiments, which will launch jobs through the `Flux resource manager <https://flux-framework.org/>`_::

    ramble --disable-progress-bar --workspace-dir /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace on

You should receive something like this on the terminal after running the command::

    ==> Streaming details to log:
    ==>   /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace/logs/execute.2025-07-09_18.14.08.out
    ==>   Executing 4 out of 4 experiments:
    ==>   Log files for experiments are stored in: /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace/logs/execute.2025-07-09_18.14.08
    ==> Running executors...
    ƒV54uD5o5  
    ƒV57fKkEK  
    ƒV5ANUS6s  
    ƒV5D498h5

.. note::

    You can check on the progress of your runs by running the command::

        flux jobs [-a]


The experiments will run sequentially, and the total time to complete all four experiments should be 8-9 minutes. Upon completion, each
experiment will generate a caliper file. When all the experiments are finished, running the command :code:`flux jobs -a` will show all the
jobs. A completed job will be green with ``CD`` as its status (Example below):

    .. image:: ./finished_experiments_example.png
       :alt: Example output of flux jobs -a when experiments are finished
       :width: 750px
       :align: center

8. After running the experiments, conduct pre-defined analysis with Benchpark::

    benchpark analyze --workspace-dir ~/benchpark/wkp/kripke-benchmark/tutorial/workspace

9. Navigate to ``~/benchpark/wkp/kripke-benchmark/tutorial/workspace/analyze``. This directory will contain the results from the analysis,
   including the graph below:

    .. image:: ./kripke_mpi_strong_raw_exc.png
       :alt: Kripke Analysis Graph
       :width: 900px
       :align: center