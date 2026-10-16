..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

.. _beginner-tutorial-glossary:

.. _beginner-tutorial-start-here:

############
 Start Here
############

.. tutorialcontainer:: tutorial-project-links

    .. tutorialcontainer:: tutorial-project-link

        .. rubric:: Benchpark Source

        .. image:: /_static/images/benchpark-icon.svg
            :alt: Benchpark on GitHub
            :target: https://github.com/llnl/benchpark

    .. tutorialcontainer:: tutorial-project-link

        .. rubric:: Benchpark Tutorial Slides

        .. image:: tutorial/HPCIC26-Tutorial-Slide-Preview.jpg
            :alt: Benchpark Tutorial Slides
            :target: _static/slides/HPCIC26-Tutorial-Slides.pdf

    .. tutorialcontainer:: tutorial-project-link

        .. rubric:: Benchpark on CDash

        .. image:: /_static/images/cdash.svg
            :alt: Benchpark CDash
            :target: https://my.cdash.org/index.php?project=Benchpark

    .. tutorialcontainer:: tutorial-project-link

        .. rubric:: Spack

        .. image:: https://spack.readthedocs.io/en/latest/_static/spack-logo-text.svg
            :alt: Spack
            :target: https://spack.readthedocs.io/en/latest/

    .. tutorialcontainer:: tutorial-project-link

        .. rubric:: Ramble

        .. image:: https://avatars.githubusercontent.com/u/318055132?s=60&v=4
            :alt: Ramble
            :target: https://ramble.readthedocs.io/en/latest/

|

********************
 Benchpark Glossary
********************

The Beginner Tutorial uses the following terms from Spack, Ramble, and Benchpark:

.. list-table::
    :header-rows: 1
    :widths: 18 18 64

    - - Name
      - Source
      - Definition
    - - .. tutorialtarget:: beginner-tutorial-glossary-benchmark

        **Benchmark**

      - General
      - The source code of a program that tests the performance of hardware and
        software.
    - - .. tutorialtarget:: beginner-tutorial-glossary-package

        **Package**

      - `Spack
        <https://spack.readthedocs.io/en/latest/packaging_guide_creation.html#structure-of-a-package>`__
      - A Python module named ``package.py`` that records a recipe or installation
        script detailing exactly how to download, build, test, and deploy a specific
        piece of software from source code.
    - - .. tutorialtarget:: beginner-tutorial-glossary-spec

        **Spec**

      - `Spack <https://spack.readthedocs.io/en/latest/spec_syntax.html>`__
      - A description of a particular build configuration of a package. A spec can
        constrain properties including the package version, compiler, variants,
        architecture, and dependencies.
    - - .. tutorialtarget:: beginner-tutorial-glossary-variant

        **Variant**

      - `Spack <https://spack.readthedocs.io/en/latest/spec_syntax.html#variants>`__
      - A named, configurable option that controls how a package is built. A variant can
        be Boolean, single-valued, or multi-valued.
    - - .. tutorialtarget:: beginner-tutorial-glossary-application

        **Application**

      - `Ramble
        <https://ramble.readthedocs.io/en/latest/getting_started.html#application-workloads>`_
      - A Python module named ``application.py`` that records a recipe or runtime script
        detailing exactly how to configure the runtime parameters of a program, execute
        it, and analyze its figure of merit.
    - - .. tutorialtarget:: beginner-tutorial-glossary-experiment

        **Experiment**

      - :doc:`Benchpark <add-an-experiment>`
      - A Python module named ``experiment.py`` that records the programming model(s) a
        given benchmark uses to parallelize execution on a node, how to scale the
        benchmark (strong scaling, weak scaling, throughput), and what type of
        instrumentation can be enabled in the benchmark.
    - - .. tutorialtarget:: beginner-tutorial-glossary-system

        **System**

      - :doc:`Benchpark <add-a-system-config>`
      - A Python module named ``system.py`` that records the hardware resources,
        scheduler, and system software for a specific HPC system (machine) or group of
        systems.
    - - .. tutorialtarget:: beginner-tutorial-glossary-modifier

        **Modifier**

      - :doc:`Benchpark </modifiers>`
      - A reusable object that can inject commands before, after, or during experiment
        execution to capture available system resources or experiment data and metadata,
        record Linux thread and GPU affinity, or inject performance analysis tools.
    - - .. tutorialtarget:: beginner-tutorial-glossary-scaling-study

        **Scaling Study**

      - :doc:`Benchpark <add-a-scaling-configuration>`
      - A set of related experiments that varies allocated resources and/or problem
        size. Benchpark supports strong scaling (varying number of processes or threads
        for a constant size problem), weak scaling (varying number of processes while
        keeping the per-process problem size constant), and throughput scaling (varying
        the problem size while keeping the number of processes constant).

Benchpark provides a ``system.py`` to describe a system, and an ``experiment.py`` to
describe how to map a benchmark onto this system. Benchpark uses a Spack ``package.py``
to build and a Ramble ``application.py`` to run the benchmark.

.. _benchpark-spec-syntax:

*********************
  Spack Spec Syntax
*********************

A Spack package spec can include versions, architecture constraints, compiler constraints, 
and dependencies, in addition to it's package name and variants.

.. figure:: /_static/images/spack-spec_anatomy.svg
    :alt: Spack package spec: package name, versions, variants, architecture, compiler, and dependencies.
    :width: 100%
    :align: center

|

*************************
  Benchpark System Spec
*************************

A Benchpark spec describes a Benchpark object. A system spec selects a definition under
``systems/``, and an experiment spec selects a definition under ``experiments/``.

Benchpark's parser is derived from Spack's spec parser, and implements the object name and variant
portions of this syntax <https://spack.readthedocs.io/en/latest/spec_syntax.html#variants>`_.
Every token after the system or experiment name is a Benchpark variant. 
Tokens beginning with ``+`` are Boolean variants, while tokens containing ``=`` are named variants.
``compiler=cce`` and ``version=2.3-caliper`` are named variants defined by their
Benchpark objects. They are not Spack compiler (``%``) or version (``@``) constraints.

.. figure:: /_static/images/system-spec.png
    :alt: Annotated Benchpark system spec
    :width: 100%
    :align: center

|

*****************************
  Benchpark Experiment Spec
*****************************

.. figure:: /_static/images/experiment-spec.png
    :alt: Annotated Benchpark experiment spec
    :width: 100%
    :align: center

|

.. list-table:: Differences in Benchpark and Spack Specs
    :header-rows: 1
    :widths: 27 36 37

    - - Goal
      - Benchpark
      - Spack
    - - Select a version
      - Use a definition's variant: ``version=<value>``
      - Use a version constraint: ``@<version>``.
    - - Select multiple values exactly
      - Use ``<variant>=<value1>,<value2>``.
      - Use ``<variant>:=<value1>,<value2>``. In Spack, ``:=`` permits additional
        values
    - - compiler
      - Not applicable
      - ``%``
    - - dependency
      - Not applicable
      - ``^``
    - - installed-spec hash
      - Not applicable
      - ``/hash``

|

************************************************
 Continue with the step that matches your goal
************************************************

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-search

        :doc:`I want to search what is available in Benchpark.
        .. class:: text-right

        5 min.
        <search-benchpark>`

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-run

        :doc:`I want to run an experiment someone gave me on the same system.
        .. class:: text-right

        10 min.
        <build-and-run-experiment>`

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-analyze

        :doc:`I want to generate preconfigured performance figures for an experiment
        on my system. 
        .. class:: text-right

        10 min + 10 min.
        <benchpark-analyze>`

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-experiment

        :doc:`I want to run a new benchmark on the system I have
        benchmarked before.
        .. class:: text-right

        20 min.
        <add-an-experiment>`

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-update-system

        :doc:`I want to rerun my experiment on a system, but the system software stack
        has changed since I last ran it. <update-system-config>`

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-system

        :doc:`I want to run an experiment someone gave me, but on my system that has
        different hardware/software. <add-a-system-config>`

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-scaling

        :doc:`I want to run a scaling study of an experiment on my system, but there
        aren't any scaling options defined for the experiment.
        <add-a-scaling-configuration>`

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-query

        :doc:`I want to generate raw performance data to make my own figures.
        <benchpark-query>`
