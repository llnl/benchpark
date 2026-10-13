..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

.. _beginner-tutorial-glossary:

#####################
 Start Here
#####################

***********************
 Benchpark Glossary
***********************

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

Benchpark's parser is derived from Spack's spec parser. A Spack package spec can include
versions, architecture constraints, compiler constraints, and dependencies in addition
to its package name and variants:

.. figure:: /_static/images/spack-spec_anatomy.svg
    :alt: Anatomy of a Spack package spec, showing its package name, versions, variants,
        architecture, compiler, and dependencies.
    :width: 100%
    :align: center

    Anatomy of a Spack package spec.

Source: `Spack Spec Syntax
<https://spack.readthedocs.io/en/latest/spec_syntax.html#spec-syntax>`_.

Benchpark implements only the object-name and variant portions of this syntax. The
following examples show the name, Boolean variants, and named variants in Benchpark
system and experiment specs:

.. figure:: /_static/images/system-spec.png
    :alt: Benchpark system spec with a system name, a Boolean variant, and several named
        variants.
    :width: 100%
    :align: center

    Benchpark system spec.

.. figure:: /_static/images/experiment-spec.png
    :alt: Benchpark experiment spec with an experiment name, a Boolean variant, and
        named variants.
    :width: 100%
    :align: center

    Benchpark experiment spec.

In these examples, the red text is the system or experiment name, the green text is a
Boolean variant, and the orange text contains named variants. ``compiler=cce`` and
``version=2.3-caliper`` are named variants defined by their Benchpark objects. They are
not Spack compiler (``%``) or version (``@``) constraints.

A Benchpark spec describes a Benchpark object. It is distinct from the Spack package
specs that Benchpark later writes into the generated configuration. A system spec
selects a definition under ``systems/``, while an experiment spec selects a definition
under ``experiments/``.

Benchpark does not implement Spack's version (``@``), compiler (``%``), architecture,
dependency (``^``), or installed-spec hash (``/hash``) constraint semantics. It also
does not accept exact multi-value constraints (``:=``) or variant propagation (``++``
and ``==``). Benchpark uses the same basic syntax as Spack for `Boolean, single-valued,
and multi-valued variants
<https://spack.readthedocs.io/en/latest/spec_syntax.html#variants>`_.

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

***********************
 Choose Your Next Step
***********************

Continue with the step that matches your goal:

.. container:: tutorial-next-steps

    .. container:: tutorial-next-step tutorial-goal-search

        :doc:`I want to search what is available in Benchpark. <search-benchpark>`

    .. container:: tutorial-next-step tutorial-goal-run

        :doc:`I want to run an experiment someone gave me on the same system.
        <build-and-run-experiment>`

    .. container:: tutorial-next-step tutorial-goal-analyze

        :doc:`I want to generate preconfigured performance figures for an experiment
        on my system. <benchpark-analyze>`

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

    .. container:: tutorial-next-step tutorial-goal-query

        :doc:`I want to generate raw performance data to make my own figures.
        <benchpark-query>`
