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

The Beginner Tutorial uses the following terms from Spack, Ramble, and Benchpark:

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

        **Package**
      - `Spack
        <https://spack.readthedocs.io/en/latest/packaging_guide_creation.html#structure-of-a-package>`_
      - A Python module named ``package.py`` that records a recipe or installation script detailing exactly 
        how to download, build, test, and deploy a specific piece of software from source code.
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

        **Application**
      - `Ramble
        <https://ramble.readthedocs.io/en/latest/getting_started.html#application-workloads>`_
      - A Python module named ``application.py`` that records a recipe or runtime script detailing exactly
        how to configure the runtime parameters of a program, execute it, and analyze its figure of merit.
    - - .. _beginner-tutorial-glossary-package:

        **Experiment**
      - :doc:`Benchpark <add-an-experiment>`
      - A Python module named ``experiment.py`` that records the programming model(s) 
        a given benchmark uses to parallelize execution on a node, how to scale the benchmark
        (strong scaling, weak scaling, throughput), and what type of instrumentation
        can be enabled in the benchmark.
    - - .. _beginner-tutorial-glossary-system:

        **System**
      - :doc:`Benchpark <add-a-system-config>`
      - A Python module named ``system.py`` that records the hardware resources, scheduler, and
        system software for a specific HPC system (machine) or group of systems.
    - - .. _beginner-tutorial-glossary-modifier:

        **Modifier**
      - :doc:`Benchpark </modifiers>`
      - A reusable object that can inject commands before, after, or during experiment execution
        to capture available system resources or experiment data and metadata, record Linux thread
        and GPU affinity, or inject performance analysis tools.
    - - .. _beginner-tutorial-glossary-scaling-study:

        **Scaling Study**
      - :ref:`Benchpark <step-3b-define-scaling-options>`
      - A set of related experiments that varies allocated resources and/or problem size. 
        Benchpark supports strong scaling (varying number of processes or threads for a constant size problem), 
        weak scaling (varying number of processes while keeping the per-process problem size constant),
        and throughput scaling (varying the problem size while keeping the number of processes constant).

Benchpark provides a ``system.py`` to describe a system, and an ``experiment.py`` to describe how to
map a benchmark onto this system.
Benchpark uses a Spack ``package.py`` to build and a Ramble ``application.py`` to run the benchmark.


.. _benchpark-spec-syntax:

***********************
 Benchpark Spec Syntax
***********************

Benchpark's parser is derived from Spack's spec parser. A Spack package spec can include versions, architecture
constraints, compiler constraints, and dependencies, in addition to it's package name and variants:

**Spack Spec Syntax `Source <https://spack.readthedocs.io/en/latest/spec_syntax.html#spec-syntax>`_**

.. figure:: /_static/images/spack-spec_anatomy.svg
    :alt: Spack package spec: package name, versions, variants, architecture, compiler, and dependencies.
    :width: 100%
    :align: center

Benchpark implements the object name and variant portions of this syntax. The following examples show
the name, Boolean variants, and named variants in Benchpark system and experiment specs:

**Benchpark System Spec**

.. figure:: /_static/images/system-spec.png
    :alt: Benchpark system spec with a system name, a Boolean variant, and named variants.
    :width: 100%
    :align: center


**Benchpark Experiment Spec**

.. figure:: /_static/images/experiment-spec.png
    :alt: Benchpark experiment spec with an experiment name, a Boolean variant, and named variants.
    :width: 100%
    :align: center

In these examples, the red text is the system or experiment name, the green text is a
Boolean variant, and the orange text contains named variants. ``compiler=cce`` and
``version=2.3-caliper`` are named variants defined by their Benchpark objects. They are
not Spack compiler (``%``) or version (``@``) constraints.

A Benchpark spec describes a Benchpark object. A system spec selects a definition under
``systems/``, and an experiment spec selects a definition under ``experiments/``.

Benchpark does not implement Spack's version (``@``), compiler (``%``), architecture,
dependency (``^``), or installed-spec hash (``/hash``) constraint semantics. It also
does not accept exact multi-value constraints (``:=``) or variant propagation (``++``
and ``==``). Benchpark uses the same basic syntax as Spack for `Boolean, single-valued,
and multi-valued variants
<https://spack.readthedocs.io/en/latest/spec_syntax.html#variants>`_.

.. list-table:: Differences in Benchpark and Spack Specs:
    :header-rows: 1
    :widths: 27 36 37

    - - Goal
      - Benchpark
      - Spack
    - - Select a version
      - Use a definition's variant: ``version=<value>``.
      - Use a version constraint: ``@<version>``.
    - - Select multiple values exactly
      - Use ``<variant>=<value1>,<value2>``. 
      - Use ``<variant>:=<value1>,<value2>``. In Spack, ``:=`` permits additional
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
