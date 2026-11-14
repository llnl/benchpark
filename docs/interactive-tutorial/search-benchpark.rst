..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

.. _search-benchpark:

##################################################
 Search What Is Available in Benchpark and Ramble
##################################################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`,
:ref:`Variant <beginner-tutorial-glossary-variant>`, :ref:`Experiment
<beginner-tutorial-glossary-experiment>`, :ref:`System
<beginner-tutorial-glossary-system>`, :ref:`Modifier
<beginner-tutorial-glossary-modifier>`

***********
 Benchpark
***********

All of the systems, benchmarks, experiments, and modifiers that are available in
Benchpark can be searched on the command line. The ``benchpark list`` command accepts
one of four options:

.. code-block:: console

    ~]$ benchpark list {benchmarks,experiments,modifiers,systems}

The Benchpark Catalogue shows detailed information on :doc:`Benchpark Systems
</system-list>` and :doc:`Benchpark Experiments </benchmark-list>` in tabular form.

Benchpark System
================

.. figure:: /_static/images/system_slide.png
    :alt: Benchpark system class
    :figclass: tutorial-system-figure
    :width: 100%
    :align: center

A Benchpark system is initialized from a specification written in Benchpark's spec syntax. Its
definition under ``systems/`` describes the hardware resources and software stack used
to run benchmarks, including:

- Resources (CPU cores, GPUs)
- Scheduler (Slurm, flux)
- Process mapping (cores, sockets, GPUs, NICs)
- On-node parallelism (CUDA, ROCM, OpenMP)
- Software stack
- Compilers (which is best?)
- MPI implementations (best?)
- Math libraries

.. figure:: /_static/images/system-spec.png
    :alt: Annotated Benchpark system spec
    :figclass: tutorial-spec-figure
    :width: 100%
    :align: center

To search for systems in Benchpark:

.. code-block:: console

    ~]$ benchpark list systems

Benchpark Experiment
====================

.. figure:: /_static/images/experiment_slide.png
    :alt: Benchpark experiment class
    :figclass: tutorial-experiment-figure
    :width: 100%
    :align: center

A Benchpark experiment is initialized from a specification written in Benchpark's spec syntax.
Its definition under ``experiments/`` describes the information needed for reproducible
sets of experiments that can be mapped onto specific systems, including:

- On-node parallelism (CUDA, ROCM, OpenMP)
- Problem sizes

      - Overall problem size, or
      - Per node or per GPU

- Scaling studies

  - How to scale
  - How to decompose

- Resources (cores, GPUs)

.. figure:: /_static/images/experiment-spec.png
    :alt: Annotated Benchpark experiment spec
    :figclass: tutorial-spec-figure
    :width: 100%
    :align: center

Use the filter to find experiments with your targeted programming model or specific type
of scaling. For example, this command will display only the CUDA experiments:

.. code-block:: console

    ~]$ benchpark list experiments --experiment cuda

After choosing a system or experiment, inspect its variants and configuration details:

.. code-block:: console

    ~]$ benchpark info system fluxtainer-aws
    ~]$ benchpark info experiment hpl

To find systems with a specific CPU architecture, query their system resources:

.. code-block:: console

    $ benchpark info system --query cpu_arch=sapphirerapids
    cpu_arch=sapphirerapids:
        aws-tutorial: c7i.48xlarge
        aws-tutorial: c7i.metal-48xl
        aws-tutorial: c7i.24xlarge
        aws-tutorial: c7i.metal-24xl
        aws-tutorial: c7i.12xlarge
        llnl-cluster: dane
        llnl-cluster: poodle-deprecated
        llnl-matrix: matrix
        lanl-rocinante: crossroads
        lanl-rocinante: rocinante
        lanl-rocinante: tycho

For a complete command reference, see :doc:`Benchpark Commands </benchpark-commands>`.

********
 Ramble
********

Ramble is primarily controlled through the ``ramble`` command. Whenever you want to see
available commands or learn about command-specific flags, you can use Ramble's built-in
help system.

To view the most common commands and global flags:

.. code-block:: console

    $ ramble --help

To see the complete list of all Ramble commands grouped by category (including
developer, configuration, and workspace commands):

.. code-block:: console

    $ ramble help --all

Any command or subcommand accepts ``--help`` (or ``-h``) to display detailed usage
information. For example, to explore the options for ``ramble list`` or ``ramble
workspace``:

.. code-block:: console

    $ ramble list --help
    $ ramble workspace --help

Listing and Searching Objects (``ramble list``)
===============================================

Listing Applications
--------------------

To see all applications currently available in your configured Ramble repositories, run:

.. code-block:: console

    $ ramble list

By default, ``ramble list`` prints every available application. You can narrow the
results by providing one or more case-insensitive filter arguments.

Substring and Glob Filtering
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Passing a plain word searches for any application whose name contains that substring.
For example, to list all applications containing the letter ``h``:

.. code-block:: console

    $ ramble list h

which produces:

.. figure:: /_static/ramble_snippets/ramble_basics_hostname_list_h.png
    :alt: List all applications containing the letter h in Ramble
    :width: 50%
    :align: center

You can also use shell glob characters such as ``*`` and ``?`` (wrapped in quotes so
your shell does not expand them before passing them to Ramble). For example, to list
only applications whose names **start** with ``h``:

.. code-block:: console

    $ ramble list "h*"

which produces:

.. figure:: /_static/ramble_snippets/ramble_basics_hostname_list_hstar.png
    :alt: List all applications that start with the letter h in Ramble
    :width: 50%
    :align: center

Searching Descriptions
^^^^^^^^^^^^^^^^^^^^^^

If you know the domain or functionality you are looking for rather than the exact
application name, add the ``-d`` (``--search-description``) flag to search both
application names and docstrings/descriptions:

.. code-block:: console

    $ ramble list -d "molecular dynamics"

Filtering by Tags
^^^^^^^^^^^^^^^^^

Every object in Ramble can be annotated with descriptive tags (information on how to see
what tags are available will be provided later in this tutorial). You can filter
``ramble list`` by tag using ``-t`` (``--tags``):

.. code-block:: console

    $ ramble list -t test-app

which outputs:

.. figure:: /_static/ramble_snippets/ramble_basics_hostname_list_tag.png
    :alt: List all applications that have a particular tag
    :width: 50%
    :align: center

Listing Other Object Types
--------------------------

To list objects other than applications, pass ``--type <object_type>`` to ``ramble
list``.

For example, to list all available **modifiers**:

.. code-block:: console

    $ ramble list --type modifiers

which produces:

.. figure:: /_static/ramble_snippets/ramble_basics_hostname_list_modifiers.png
    :alt: List all modifiers in Ramble
    :width: 50%
    :align: center

To list all available **package managers**:

.. code-block:: console

    $ ramble list --type package_managers

.. figure:: /_static/ramble_snippets/ramble_basics_hostname_list_package_managers.png
    :alt: List all package managers in Ramble
    :width: 50%
    :align: center

And to list all available **workflow managers**:

.. code-block:: console

    $ ramble list --type workflow_managers

.. figure:: /_static/ramble_snippets/ramble_basics_hostname_list_workflow_managers.png
    :alt: List all workflow managers in Ramble
    :width: 50%
    :align: center

Inspecting Object Details (``ramble info``)
===========================================

Once you have identified an application or modifier of interest using ``ramble list``,
use ``ramble info`` to inspect its structure, workloads, tunable variables, software
specs, and figures of merit.

Viewing an Application Summary
------------------------------

Let's inspect the ``hostname`` application:

.. code-block:: console

    $ ramble info hostname

This command prints a comprehensive overview of the ``hostname`` application:

.. figure:: /_static/ramble_snippets/ramble_basics_hostname_info.png
    :alt: Overview of ``hostname`` application
    :width: 50%
    :align: center

From this output, you can see:

- **Description**: What the application does.
- **Tags**: Metadata tags associated with the application (``test-app``).
- **Workloads**: Named execution scenarios supported by the application (``local``,
  ``parallel``, ``serial``), along with their associated executables and inputs.
- **Figures of Merit**: Performance or validation metrics that Ramble automatically
  extracts when analyzing experiment output (``possible hostname``).
- **Success Criteria**: Conditions Ramble checks to determine whether an experiment
  succeeded (``wrote_anything``).
- **Builtin Executables**: Internal steps injected into the execution pipeline
  (``builtin::env_vars``). These are defined in either the application definition, or
  one of it's ancestors.

Inspecting Modifiers and Other Objects
--------------------------------------

Just like ``ramble list``, ``ramble info`` can inspect any object type using ``--type
<object_type>`` or a fully qualified namespace spec (such as ``builtin.mod.<name>``).

For example, to inspect the ``lscpu`` modifier:

.. code-block:: console

    $ ramble info --type modifiers lscpu

or equivalently:

.. code-block:: console

    $ ramble info builtin.mod.lscpu

which produces:

.. figure:: /_static/ramble_snippets/ramble_basics_hostname_info_modifier_lscpu.png
    :alt: Inspect an object time
    :width: 50%
    :align: center

For more information, see `Ramble Basics
<https://ramble.readthedocs.io/en/latest/tutorials/beginner_ramble_basics.html>`_.

**********************
 Return to Start Here
**********************

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-start

        :doc:`I want to return to the start page. <start-here>`
