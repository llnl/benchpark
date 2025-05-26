.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

For each ``experiment`` (``benchmark`` x ``ProgrammingModel`` x ),
Ramble sets up the following ``workspace`` directory structure
to build and run the experiment::

    experiments_root/
        ramble/
        spack/
        <benchmark>/
            <ProgrammingModel>/
                <system>/
                    workspace/
                        configs/
                            (everything from system_def_dir)
                            (everything from experiment_def_dir)
                        experiments/
                            <benchmark>/
                                <problem>/
                                    <benchmark>_<ProgrammingModel>_<problem>
                                        execute_experiment
