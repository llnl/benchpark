..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

########################
 Adding a Spack Package
########################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`,
:ref:`Package <beginner-tutorial-glossary-package>`

A Spack ``package.py`` defines how to download, build, and install a benchmark. If a
package already exists in the `Spack Packages repository <https://packages.spack.io>`_,
Benchpark uses that definition. A package in
``repos/spack_repo/benchpark/packages/<benchmark-name>/package.py`` overrides the
corresponding upstream package.

For the HPL example, create ``repos/spack_repo/benchpark/packages/hpl/package.py`` with
the following complete contents:

.. literalinclude:: ../../repos/spack_repo/benchpark/packages/hpl/package.py
    :language: python
    :linenos:

For a benchmark without an upstream package, follow the `Spack Package Creation
Tutorial <https://spack-tutorial.readthedocs.io/en/latest/tutorial_packaging.html>`_ to
create and test its ``package.py``.

Before adding the experiment, create its :doc:`Ramble application
<add-a-ramble-application>` if one is also missing.

**********
 Next Step
**********

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-experiment

        :doc:`My Spack package and Ramble application are defined. I want to add the
        experiment. <add-an-experiment>`
