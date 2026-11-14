..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

.. _beginner-tutorial-glossary:

.. _beginner-tutorial-start-here:

############
 Start Here
############

Benchpark is an open-source infrastructure-as-code Python project which aims to enable
reproducibility in HPC benchmarking. It accomplishes this by defining each component of
HPC benchmarking, and constraining it separately. Benchpark builds on the specifications
provided by Spack, an HPC package manager, and Ramble, an HPC testing framework.

.. seealso::

    `Latest Benchpark Tutorial Slides <../_static/slides/PACT26-Tutorial-Slides.pdf>`_ |
    `Benchpark Code on GitHub <https://github.com/llnl/benchpark>`_ | `Benchpark
    Dashboard <https://my.cdash.org/index.php?project=Benchpark>`_ | `Ramble
    <https://ramble.readthedocs.io/en/latest/>`_ | `Spack
    <https://spack.readthedocs.io/en/latest/>`_

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
    - - .. tutorialtarget:: beginner-tutorial-glossary-modifier

        **Modifier**

      - `Ramble
        <https://ramble.readthedocs.io/en/latest/tutorials/intermediate_using_modifiers.html#discovering-modifiers>`__
      - An object that encapsulates reusable experiment configuration. Benchpark
        provides modifier implementations, including Caliper and Allocation, that follow
        Ramble's modifier syntax. These modifiers can inject commands before, after, or
        during experiment execution to capture system resources, experiment data, and
        metadata, or to enable performance analysis tools. See :doc:`Benchpark Modifiers
        </modifiers>`.
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

***********************************************
 Continue with the step that matches your goal
***********************************************

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-search tutorial-with-duration

        :doc:`I want to search what is available in Benchpark and Ramble. <search-benchpark>`

        .. tutorialcontainer:: tutorial-duration

            10 min.

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-run tutorial-with-duration

        :doc:`I want to run an experiment someone gave me on the same system.
        <build-and-run-experiment>`

        .. tutorialcontainer:: tutorial-duration

            25 min.

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-troubleshoot tutorial-with-duration

        :doc:`I ran into an error while running an experiment someone gave me
        on the same system, and want to learn how to diagnose it. <troubleshoot-a-failed-run>`

        .. tutorialcontainer:: tutorial-duration

            25 min.

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-analyze tutorial-with-duration

        :doc:`I want to generate preconfigured performance figures for an experiment
        on my system. <benchpark-analyze>`

        .. tutorialcontainer:: tutorial-duration

            (#2 or #3) + 15 min.

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-run-substitute tutorial-with-duration

        :doc:`I want to run an experiment, but build it with a different compiler
        or library (e.g., gcc or clang compiler). <build-and-run-with-clang>`

        .. tutorialcontainer:: tutorial-duration

            25 min.

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-parameter-sweep tutorial-with-duration

        :doc:`I want to perform a parameter sweep for an experiment on my system.
        <perform-a-parameter-sweep>`

        .. tutorialcontainer:: tutorial-duration

            15 min.

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-update-system

        :doc:`I want to rerun my experiment on a system, but the system software stack
        needs an update since it has changed since I last ran it. <update-system-config>`

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

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-experiment tutorial-with-duration

        :doc:`I want to run a new benchmark on the system I have benchmarked before.
        <add-an-experiment>`

        .. tutorialcontainer:: tutorial-duration

            20 min.
