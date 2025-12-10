..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

####################
 Set up a Workspace
####################

To setup an experiment workspace you must first initialize the system you will be
running on. Next, initialize the experiment you plan to run with the appropriate
programming model. Finally, set up the workspace in a directory for your experiment.:

::

    benchpark system init --dest=</output/path/to/system_def_dir/mySystemName> <SystemName> compiler=<Compiler>
    benchpark experiment init <mySystemName> <Benchmark> +/~<Boolean Variant> <String Variant>=<value>
    benchpark setup <mySystemName>/<Benchmark> </output/path/to/workspace>

where:

- ``<Benchmark>``: amg2023 | saxpy | etc. (specified choices in :doc:`benchmark-list`)
- ``<SystemName>``: Cts | Tioga | etc. (specified systems in :doc:`system-list`)

This command will assemble a Ramble workspace per experiment with a configuration for
the specified benchmark and system with the following directory structure:

::

    experiments_root/
        ramble/
        spack/
        <System>/
            <Benchmark/ProgrammingModel>/
                workspace/
                    configs/
                        (everything from system_def_dir)
                        (everything from experiment_def_dir>)

``benchpark setup`` will output instructions to follow:

::

    . <experiments_root>/setup.sh

The ``setup.sh`` script calls the Spack and Ramble setup scripts. It optionally accepts
parameters to ``ramble workspace setup`` as `documented in Ramble
<https://ramble.readthedocs.io/en/latest/getting_started.html#setting-up-a-workspace>`_,
including ``--dry-run`` and ``--phases make_experiments``.

Now you are ready to compile your experiments as described in :doc:`build-experiment`.

*************************************
 Built-in System/Experiment Variants
*************************************

There are benchpark system and experiment variants that you can change, without needing
to define them in your ``system.py`` and ``experiment.py``.

#############
 For Systems
#############

    - ``timeout`` - Job timeout limit in minutes.

#################
 For Experiments
#################

    - ``package_manager`` - Specify this variant to use a ramble package manager other
      than ``spack``. See :doc:`run-binary` to see an example.
    - ``append_path`` - Append to environment PATH during experiment execution.
    - ``prepend_path`` - Prepend to environment PATH during experiment execution.
    - ``n_repeats`` - number of times your experiment will be repeated (think of
      trials). ``n_repeats=5`` will repeat your experiment 5 times, resulting in 5
      trials. These will be separate job submission scripts, so separate resource
      allocations. For combining these into the same allocation, see TBD.
