..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

.. _beginner-tutorial-glossary:

#####################
 Benchpark Glossary
#####################

The Beginner Tutorial uses terms from Benchpark, Ramble, and Spack. This table defines
how the tutorial uses each term and identifies the project that provides the underlying
concept.

.. list-table::
    :header-rows: 1
    :widths: 18 18 64

    - - Name
      - Source
      - Definition
    - - .. _beginner-tutorial-glossary-benchmark:

        **Benchmark**
      - General
      - The source code of a program that tests the performance of hardware and
        software.
    - - .. _beginner-tutorial-glossary-application:

        **Application**
      - `Ramble
        <https://ramble.readthedocs.io/en/latest/getting_started.html#application-workloads>`_
      - A Ramble object that describes how to configure, execute, and analyze a program.
        An application defines one or more workloads from which Ramble experiments can
        be generated.
    - - .. _beginner-tutorial-glossary-package:

        **Package**
      - `Spack
        <https://spack.readthedocs.io/en/latest/packaging_guide_creation.html#structure-of-a-package>`_
      - A Python module named ``package.py`` that describes how to build and test
        software according to a Spack spec. It contains the software metadata,
        dependencies, variants, and build behavior.
    - - .. _beginner-tutorial-glossary-spec:

        **Spec**
      - `Spack
        <https://spack.readthedocs.io/en/latest/spec_syntax.html>`_
      - A description of a particular build configuration of a package. A spec can
        constrain properties including the package version, compiler, variants,
        architecture, and dependencies.
    - - .. _beginner-tutorial-glossary-variant:

        **Variant**
      - `Spack
        <https://spack.readthedocs.io/en/latest/spec_syntax.html#variants>`_
      - A named, configurable option that controls how a package is built. A variant can
        be Boolean, single-valued, or multi-valued.
    - - .. _beginner-tutorial-glossary-experiment:

        **Experiment**
      - :doc:`Benchpark <add-an-experiment>`
      - A Benchpark ``experiment.py`` definition that selects a benchmark workload and
        describes its programming model, scaling behavior, variables, instrumentation,
        and generated Ramble experiments.
    - - .. _beginner-tutorial-glossary-system:

        **System**
      - :doc:`Benchpark <add-a-system-config>`
      - A Benchpark ``system.py`` definition of the hardware resources, scheduler, and
        software configurations for a target machine or group of machines.
    - - .. _beginner-tutorial-glossary-modifier:

        **Modifier**
      - :doc:`Benchpark </modifiers>`
      - A reusable configuration that can be applied to experiments. A modifier can
        inject performance instrumentation, configure runtime behavior, or set up
        system resources.
    - - .. _beginner-tutorial-glossary-scaling-study:

        **Scaling Study**
      - :ref:`Benchpark <step-3b-define-scaling-options>`
      - A set of related experiments that varies allocated resources and, depending on
        the scaling mode, problem size. Benchpark supports strong, weak, and throughput
        scaling studies.

Ramble does not define an object named ``Benchmark``. Benchpark uses a Ramble
application to describe how a benchmark is executed and a Spack package to describe how
it is built.

.. _benchpark-spec-syntax:

***********************
 Benchpark Spec Syntax
***********************

Benchpark uses *specs* to select a system or experiment definition and configure its
variants. You pass these specs to ``benchpark system init`` and ``benchpark experiment
init``. For example:

.. code-block:: console

    $ benchpark system init --dest=<system-id> <system> +/~<boolean-variant> <variant>=<value>
    $ benchpark experiment init <system-id> <benchmark> +/~<boolean-variant> <variant>=<value>

The first command selects a system definition and configures its variants. The second
command selects a benchmark's experiment definition and configures its variants for the
initialized system. In these templates, ``+/~`` means that a Boolean variant can be
enabled with ``+`` or disabled with ``~``.

A Benchpark spec describes a Benchpark object. It is distinct from the Spack package
specs that Benchpark later writes into the generated configuration. A system spec
selects a definition under ``systems/``, while an experiment spec selects a definition
under ``experiments/``.

Inspect Available Variants
==========================

Each system and experiment defines its own variants, allowed values, and defaults.
Inspect them before constructing a spec:

.. code-block:: console

    $ benchpark info system --variants <system>
    $ benchpark info experiment --variants <benchmark>

The ``benchpark info`` output includes variants inherited from reusable Benchpark
components, such as programming models and scaling modes. Benchpark applies default
values for omitted variants when it initializes the object. It rejects unknown variants,
unsupported values, and invalid combinations.

Write a Benchpark Spec
======================

Place the system or experiment name first, followed by zero or more variants:

.. list-table:: Benchpark spec forms
    :header-rows: 1
    :widths: 24 30 46

    - - Purpose
      - Form
      - Example
    - - Select an object
      - ``name``
      - ``<name>``
    - - Select a namespaced experiment
      - ``namespace.name``
      - ``<namespace>.<name>``
    - - Enable a Boolean variant
      - ``+name``
      - ``+<boolean-variant>``
    - - Disable a Boolean variant
      - ``~name``
      - ``~<boolean-variant>``
    - - Select one value
      - ``name=value``
      - ``<variant>=<value>``
    - - Select multiple values
      - ``name=value1,value2``
      - ``<variant>=<value1>,<value2>``

Boolean variants can follow the object name without a space, as in
``<name>+<boolean-variant>``. This form also prevents a shell from interpreting a
disabled variant as a home-directory expression:

.. code-block:: console

    $ benchpark experiment init <system-id> <benchmark>~<boolean-variant>

For a multi-valued Benchpark variant, the comma-separated values are the selected
values. The general form is ``<variant>=<value1>,<value2>``.

Relationship to Spack Specs
===========================

Benchpark's parser is derived from Spack's spec parser and uses the same basic syntax
for `Boolean, single-valued, and multi-valued variants
<https://spack.readthedocs.io/en/latest/spec_syntax.html#variants>`_. The complete
`Spack spec syntax <https://spack.readthedocs.io/en/latest/spec_syntax.html>`_ is not a
Benchpark language reference because Benchpark implements only the object-name and
variant subset described on this page.

In particular, Benchpark does not implement Spack's version (``@``), compiler (``%``),
architecture, dependency (``^``), or installed-spec hash (``/hash``) constraint
semantics. It also does not accept exact multi-value constraints (``:=``) or variant
propagation (``++`` and ``==``).

These related forms have different meanings in the two tools:

.. list-table:: Benchpark and Spack differences
    :header-rows: 1
    :widths: 27 36 37

    - - Goal
      - Benchpark
      - Spack
    - - Select a version
      - Use a definition's variant: ``version=<value>``.
      - Use a version constraint: ``@<version>``.
    - - Select multiple values exactly
      - Use ``<variant>=<value1>,<value2>``. Benchpark preserves the specified set.
      - Use ``<variant>:=<value1>,<value2>``. In Spack, ``=`` permits additional
        values.

.. _search-benchpark:

***************************************
 Search What Is Available in Benchpark
***************************************

All of the systems, benchmarks, experiments, and modifiers that are available in
benchpark can be searched on the command line. The ``benchpark list`` command accepts
one of four categories:

.. code-block:: console

    $ benchpark list systems
    $ benchpark list benchmarks
    $ benchpark list experiments
    $ benchpark list modifiers

The generated :doc:`system catalogue </system-list>` and :doc:`benchmark catalogue
</benchmark-list>` provide detailed information for systems and benchmarks in a tabular
form.

For searching experiments, use the filter to find your targeted programming model. For
example, this command only shows experiments that support ROCm:

.. code-block:: console

    $ benchpark list experiments --experiment rocm

The same search can be performed for ROCm systems:

.. code-block:: console

    $ benchpark list systems --programming-model rocm

After choosing a system or experiment, inspect its variants and other configuration
details:

.. code-block:: console

    $ benchpark info system <system>
    $ benchpark info experiment <experiment>

Run the command help to see all supported filters and arguments:

.. code-block:: console

    $ benchpark list --help
    $ benchpark info --help

For a complete command reference, see :doc:`Benchpark Commands </benchpark-commands>`.

***********************
 Choose Your Next Step
***********************

Continue with the step that matches your goal:

.. container:: tutorial-next-steps

    .. container:: tutorial-next-step tutorial-goal-system

        :doc:`I want to run an experiment someone gave me, but on my system that has
        different hardware/software. <add-a-system-config>`

    .. container:: tutorial-next-step tutorial-goal-update-system

        :doc:`I want to rerun my experiment on a system, but the system software stack
        has changed since I last ran it. <update-system-config>`

    .. container:: tutorial-next-step tutorial-next-step-multiple tutorial-goal-benchmark

        I want to run a :doc:`new benchmark <add-a-benchmark>` on the system I have
        benchmarked before (this also requires :doc:`adding an experiment
        <add-an-experiment>`).

    .. container:: tutorial-next-step tutorial-goal-scaling

        :ref:`I want to run a scaling study of an experiment on my system, but there
        aren't any scaling options defined for the experiment.
        <step-3b-define-scaling-options>`

    .. container:: tutorial-next-step tutorial-goal-run

        :doc:`I want to run an experiment someone gave me on the same system.
        <build-and-run-experiment>`

    .. container:: tutorial-next-step tutorial-goal-analyze

        :doc:`I want to generate preconfigured performance figures for an experiment
        on my system. <benchpark-analyze>`

    .. container:: tutorial-next-step tutorial-goal-query

        :doc:`I want to generate raw performance data to make my own figures.
        <benchpark-query>`
