..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

###################
 For the Impatient
###################

You need git and Python 3.8+:

::

    git clone https://github.com/LLNL/benchpark.git
    cd benchpark
    . setup-env.sh
    benchpark --version

    python3 -m venv my-env
    . my-env/bin/activate

    pip install -r requirements.txt

********************
 Set up a Workspace
********************

::

    benchpark system init --dest=</output/path/to/system_def_dir/mySystemName> <SystemName> compiler=<Compiler>
    benchpark experiment init <mySystemName> <Benchmark> +/~<Boolean Variant> <String Variant>=<value>
    benchpark setup <mySystemName>/<Benchmark> </output/path/to/workspace>

where:

- ``<Benchmark>``: amg2023 | saxpy | etc. (predefined choices in :doc:`benchmark-list`)
- ``<SystemName>``: Cts | Tioga | etc. (predefined systems in :doc:`system-list`)

``benchpark setup`` will output instructions to follow:

::

    . <experiments_root>/setup.sh

*********************
 Build an Experiment
*********************

::

    cd <experiments_root>/<System>/<Benchmark>/workspace
    ramble --workspace-dir . workspace setup

********************
 Run the Experiment
********************

To run all of the experiments in the workspace:

::

    ramble --workspace-dir . on

To run a single experiment in the workspace, invoke the ``execute_experiment`` script
for the specific experiment (e.g.,
``$workspace/experiments/amg2023/problem1/amg2023_cuda11.8.0_problem1_1_8_2_2_2_10_10_10/execute_experiment``).

**********************
 Experiment pass/fail
**********************

Once the experiments completed running, the command:

::

    ramble --workspace-dir . workspace analyze

can be used to analyze figures of merit and evaluate `success/failure
<https://ramble.readthedocs.io/en/latest/success_criteria.html#success-criteria>`_ of
the experiments. Ramble generates a file with summary of the results in ``$workspace``.

If the benchmark you are running is instrumented with `Caliper
<https://github.com/llnl/caliper>`_, you can use the Caliper modifier (see
:doc:`modifiers`) to collect detailed measurements you can later analyze with `Thicket
<https://github.com/llnl/thicket>`_.
