.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

=================================
Setting Up a Benchpark Workspace
=================================

To setup an experiment workspace you must first initialize both an experiment and a system to use. 
Any system or experiment variants are specified at the end of the command as shown below.
The order of the two init commands does not matter, but they both need to be run before the setup command.::

    benchpark system init --dest=</output/path/to/system_def_dir> <SystemName> compiler=<Compiler>
    benchpark experiment init --dest=</output/path/to/experiment_def_dir> <Benchmark> <Variant>=<oui/non/value>


Once you have a benchmark experiment to run, along with the programming model to use, and a system to run them on.
Also choose a directory for your experiment::

    benchpark setup </output/path/to/experiment_def> </output/path/to/system_def> </output/path/to/workspace>

where:

- ``<Benchmark>``: amg2023 | saxpy | etc. (predefined choices in :doc:`benchmark-list`)
- ``<System>``: Cts | Tioga | etc. (predefined systems in :doc:`system-list`)

This command will assemble a Ramble workspace per experiment
with a configuration for the specified benchmark and system
with the following directory structure::

    experiments_root/
        ramble/
        spack/
        <Benchmark/ProgrammingModel>/
            <System>/
                workspace/
                    configs/
                        (everything from system_def_dir)
                        (everything from experiment_def_dir>)

``benchpark setup`` will output instructions to follow::

   . <experiments_root>/setup.sh

The ``setup.sh`` script calls the Spack and Ramble setup scripts.  It optionally accepts
parameters to ``ramble workspace setup`` as `documented in Ramble
<https://ramble.readthedocs.io/en/latest/getting_started.html#setting-up-a-workspace>`_,
including ``--dry-run`` and ``--phases make_experiments``.

Now you are ready to compile your experiments as described in :doc:`build-experiment`.
