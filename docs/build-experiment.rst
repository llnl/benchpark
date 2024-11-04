.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

=====================================
Defining the Experiments in Benchpark
=====================================

``benchpark setup`` has set up the directory structure for your experiment.
The next step is setting up the Ramble workspace and building the code::

   cd <experiments_root>/<Benchmark/ProgrammingModel>/<System>/workspace
   ramble --disable-progress-bar --workspace-dir . workspace setup


Ramble will build the source code and set up the following workspace directory structure::

    experiments_root/
        ramble/
        spack/
        <Benchmark/ProgrammingModel>/
            <System>/
                workspace/
                    configs/
                        (everything from system_def_dir)
                        (everything from experiment_def_dir)
                    experiments/
                        <Benchmark>/
                           <Problem>/
                              <Benchmark>_<ProgrammingModel>_<Problem>
                                    execute_experiment

If you edit any of the files, see :doc:`FAQ` to determine
whether you need to re-do any of the previous steps.

Once that is complete, you are ready for :doc:`run-experiment`. 
