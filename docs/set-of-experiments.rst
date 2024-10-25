.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

===============================
Benchpark Suites of Experiments
===============================

You may want to use the same experiments_root directory when setting up multiple experiments:

* Benchpark only stores one copy of Spack/Ramble per experiments directory,
  and does not repeatedly download them when reusing the experiments directory.
* Since each experiment in the experiments directory shares the Spack/Ramble instances,
  the edits/updates you make to Spack packages will apply to all experiments
  in your experiments directory.

To use the same experiments directory when setting up multiple experiments,
instruct benchpark to set them up in the same experiments_root::

    benchpark setup ${Benchmark1}/${ProgrammingModel1} ${System1} /output/path/to/experiments_root
    benchpark setup ${Benchmark1}/${ProgrammingModel2} ${System2} /output/path/to/experiments_root
    benchpark setup ${Benchmark2}/${ProgrammingModel2} ${System1} /output/path/to/experiments_root

This will result in the following directory structure::

    experiments_root/
        ramble/
        spack/
        ${Benchmark1}/
            ${ProgrammingModel1}/
                ${System1}/
                    workspace/
            ${ProgrammingModel2}/
                ${System2}/
                    workspace/
        ${Benchmark2}/
            ${ProgrammingModel2}/
                ${System1}/
                    workspace/

Note that there is a single clone of Ramble, and a single clone of Spack,
which all of the ``experiments`` use.
Each ``experiment`` (``Benchmark/ProgrammingModel`` x ``system`` combination)
has its own ``Ramble workspace``, where this specific ``experiment``
will be compiled and run.
