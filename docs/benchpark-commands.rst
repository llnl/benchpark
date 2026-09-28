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
    - - benchpark list <category>
      - Lists available objects. Choose one of ``benchmarks``, ``experiments``,
        ``systems``, or ``modifiers``.
      -
    - - benchpark list systems
      - Lists all systems specified in Benchpark
      - :doc:`system-list`
    - - benchpark list benchmarks
      - Lists all benchmarks specified in Benchpark
      - :doc:`benchmark-list`
    - - benchpark list experiments
      - Lists all experiments specified in Benchpark
      - :doc:`benchmark-list`
    - - benchpark list modifiers
      - Lists all modifiers specified in Benchpark
      - :doc:`modifiers`
    - - benchpark tags
      - Lists all tags specified in Benchpark
      -
    - - benchpark tags -a application
      - Lists all tags specified for a given application in Benchpark
      -
    - - benchpark tags -t tag
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

.. list-table:: Benchpark workflow and utility commands
    :widths: 30 70
    :header-rows: 1

    - - Command
      - Description
    - - benchpark system init <system-spec>
      - Initializes a system configuration from a system spec.
    - - benchpark system id <system-dir>
      - Prints the system ID for an initialized system directory.
    - - benchpark system external <system-spec>
      - Checks packages found with ``spack external find`` against a Benchpark system
        definition.
    - - benchpark experiment init <system-dir> <experiment-spec>
      - Initializes an experiment for a generated system directory.
    - - benchpark setup <experiment> <experiments-root>
      - Sets up an experiment and prepares it to build and run.
    - - benchpark redo <system-dir> <experiments-root>
      - Re-instantiates all experiments under a system directory.
    - - benchpark aggregate --dest <out-dir> <workspace> [workspace ...]
      - Aggregates multiple experiment workspaces into one submission script.
    - - benchpark configure
      - Writes Benchpark environment configuration such as the bootstrap location.
    - - benchpark mirror create <workspace> <dest-dir>
      - Copies a Benchpark workspace and its resources into a mirror directory.
    - - benchpark show-build dump <workspace> <dest-dir>
      - Dumps logs and resources needed to inspect how Spack built a benchmark.
    - - benchpark unit-test
      - Runs Benchpark unit tests.
    - - benchpark audit
      - Looks for problems in system and experiment repositories.
    - - benchpark analyze
      - Performs pre-defined analysis on Caliper performance data after ``ramble on``.
    - - benchpark query
      - Queries Caliper files under a directory into a CSV.

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
