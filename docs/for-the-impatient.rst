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

System specifications accept ``extra_batch_opts`` for scheduler allocation options and
``extra_cmd_opts`` for launcher options. These options are appended after those defined
by the system and appear in the generated ``variables.yaml`` for every experiment using
that system. Quote each assignment when its value contains spaces or commas so the shell
passes it as one argument. For example:

::

    benchpark system init --dest=tuolumne llnl-elcapitan cluster=tuolumne \
        'extra_batch_opts=--requires=hosts:a,b' \
        'extra_cmd_opts=-o mpibind=greedy:0,verbose'

Omit either assignment to use only the system's own options. The default value for each
variant is ``none``.

Experiment variables can be overridden with ``name=value`` assignments, even when the
experiment does not declare them as variants. For example:

::

    benchpark experiment init tuolumne raja-perf+rocm n_nodes=384 n_resources=1536 n_cores_per_rank=21

Declared variant names keep their existing validation. Other assignments override
experiment and helper variable defaults, or add variables when absent. These values are
applied before scaling, so scaling starts from the supplied values. Integers and
floating-point values are converted to numbers; expressions and other strings are
preserved. Comma-separated values define a list, and shell quotes preserve values
containing spaces. For grouped variables, override the individual dimensions, such as
``npx=4 npy=2 npz=1``.

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
