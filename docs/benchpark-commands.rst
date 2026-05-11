..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#################
 Benchpark Lists
#################

The easiest way to get started with Benchpark is to run already specified experiments on
already specified systems, or to modify one that is similar. You can search through the
existing experiments and benchmarks with the below commands.

Search for available system and experiment specifications in Benchpark.

.. list-table:: Searching for specifications in Benchpark
    :widths: 25 25 50
    :header-rows: 1

    - - Command
      - Description
      - Listing in the docs
    - - benchpark list
      - Lists all benchmarks, systems, and experiments specified in Benchpark
      -
    - - benchpark list systems
      - Lists all system specified in Benchpark
      - :doc:`system-list`
    - - benchmark list benchmarks
      - Lists all benchmarks specified in Benchpark
      - :doc:`benchmark-list`
    - - benchmark list experiments
      - Lists all experiments specified in Benchpark
      - :doc:`benchmark-list`
    - - benchmark list modifiers
      - Lists all modifiers specified in Benchpark
      - :doc:`modifiers`
    - - benchpark tags workspace
      - Lists all tags specified in Benchpark
      -
    - - benchpark tags -a application workspace
      - Lists all tags specified for a given application in Benchpark
      -
    - - benchpark tags -t tag workspace
      - Lists all experiments in Benchpark with a given tag
      -
    - - benchpark info system <system>
      - Lists all information about a given system
      -
    - - benchpark info experiment <experiment>
      - Lists all information about a given experiment
      -
    - - benchpark bootstrap
      - Manually trigger bootstrapping or update the bootstrap
      -

Benchpark also has a help menu:

::

    $ benchpark --help

.. program-output:: ../bin/benchpark --help

The ``benchpark list`` command is used to search the available benchmarks, systems,
modifiers, and experiments in Benchpark.

.. program-output:: ../bin/benchpark list -h

.. program-output:: ../bin/benchpark list benchmarks
    :ellipsis: 10

.. program-output:: ../bin/benchpark list systems
    :ellipsis: 10

.. program-output:: ../bin/benchpark list modifiers

.. program-output:: ../bin/benchpark list experiments
    :ellipsis: 10

Additionally, this command can be used to search for experiments with one or more
programming models:

::

    $ benchpark list experiments --experiment openmp rocm

.. program-output:: ../bin/benchpark list experiments --experiment openmp rocm

Or search which experiments have the Caliper modifier (see :doc:`modifiers`) available:

::

    $ benchpark list modifiers

.. program-output:: ../bin/benchpark list modifiers

Now that you know the existing benchmarks and systems, you can determine your necessary
workflow in :doc:`benchpark-workflow`.
