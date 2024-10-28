.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

==================================
Running an Experiment in Benchpark
==================================

To run all of the experiments in the workspace::

   ramble --disable-progress-bar --workspace-dir . on

An output file is generated for each experiment in its unique directory::

  $workspace
  | └── experiments
  |    └── amg2023
  |        └── problem1
  |            ├── amg2023_cuda11.8.0_problem1_1_8_2_2_2_10_10_10
  |            │   ├── execute_experiment
  |            │   ├── amg2023_cuda11.8.0_problem1_1_8_2_2_2_10_10_10.out
  |            │   └── ...
  |            ├── amg2023_cuda11.8.0_problem1_2_4_2_2_2_10_10_10
  |            │   ├── execute_experiment
  |            │   ├── amg2023_cuda11.8.0_problem1_2_4_2_2_2_10_10_10.out
  |            │   └── ...
  |            ├── amg2023_cuda11.8.0_problem1_1_8_2_2_2_20_20_20
  |            │   ├── execute_experiment
  |            │   ├── amg2023_cuda11.8.0_problem1_1_8_2_2_2_20_20_20.out
  |            │   └── ...
  |            └── amg2023_cuda11.8.0_problem1_2_4_2_2_2_20_20_20
  |                ├── execute_experiment
  |                ├── amg2023_cuda11.8.0_problem1_2_4_2_2_2_20_20_20.out
  |                └── ...

An experiment instance can also be executed individually by directly invoking its ``execute_experiment`` script 
(e.g., ``$workspace/experiments/amg2023/problem1/amg2023_cuda11.8.0_problem1_1_8_2_2_2_10_10_10/execute_experiment``).

Note that re-running the experiment may overwrite any existing output files in the directory.
Further, if the benchmark has restart capability, existing output may alter the experiments
benchpark would run in the second run.  Generally, we would advise the user to remove the
``$workspace/experiments`` directory before re-running the experiments using
``ramble --disable-progress-bar --workspace-dir . on``.

Once you have run your experiment you can try :doc:`analyze-experiment`.
