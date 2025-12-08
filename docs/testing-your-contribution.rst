..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

###########################
 Testing Your Contribution
###########################

*******************
 Through GitHub CI
*******************

.. figure:: _static/images/dryruns.png
    :alt: Slide Preview
    :scale: 100%

    Fig. 1: Example Dryruns

Upon creating a pull request on `Benchpark <https://github.com/LLNL/benchpark>`_, unit
tests will automatically be generated for your experiment/system/modifier/application. A
member of the Benchpark repository will need to approve the tests to run if you are a
first time contributor. If you are contributing to benchpark you must check that your
contribution is passing the dryrun tests before your pull request will be merged. These
tests are indicated by the GitHub ``ci/run/dryrunexperiments`` (Figure 1) tests in the
pull request.

Dry run tests **do not** build your benchmark or run your experiments, they do:

1. Verify that your experiment/system is able to be initialized based on the programming
   models and scaling types you have included in your experiment class.
2. Verify that you have defined the necessary experiment variables for benchpark and
   ramble to generate your experiment.

1. If adding an experiment:

       a. Your experiment will be tested for each system that supports those programming
          models and for each scaling type that your experiment inherits.

2. If adding a system:

       a. Your system will be tested for each experiment in benchpark that is able to
          run for the programming models in ``self.programming_models``.

If all of the ``dryrunexperiments`` tests pass, your experiment/system has been
successfully tested.

******************
 Manually Testing
******************

You can manually test a system, experiment, or application using the following steps
(use an existing system/experiment/application to test against):

.. note::

    Spack ``package.py`` packages and Ramble ``application.py`` applications can be
    tested independently from Benchpark (see `Spack Package Creation Tutorial
    <https://spack-tutorial.readthedocs.io/en/latest/tutorial_packaging.html>`_ and
    `Ramble Usage While Developing
    <https://ramble.readthedocs.io/en/latest/dev_guides/application_dev_guide.html#usage-while-developing>`_).

1. ``system.py`` - Test System Initialization:
==============================================

This step will test the ``system.py`` you have created by attempting to create system
configuration files from your system definition.

::

    benchpark system init --dest=my-system my-system

2. ``experiment.py`` - Test Experiment Initialization:
======================================================

This step requires an existing system and will test the ``experiment.py`` you have
created by attempting to create an experiment configuration file ``ramble.yaml`` from
your experiment definition. If you also created an ``application.py`` the experiment
variables you defined in your ``experiment.py`` will be used by Ramble during the
``workspace setup`` step.

::

    benchpark experiment init --dest=my-experiment my-system my-experiment

3. Setup Benchpark Workspace:
=============================

The benchpark setup step does not directly test any of the components, and should
complete as long as you have completed the prior steps.

::

    benchpark setup ./my-system/my-experiment workspace/

4. ``application.py``/ ``package.py`` - Test Application and Package:
=====================================================================

Setting up a Ramble workspace will test your ``application.py`` and if successful, will
attempt to build your application using \*Spack. We recommend first testing your
``package.py`` separately using Spack. This step will also indirectly test your
``experiment.py`` and will fail if your ``application.py`` expects experiment variables
that you did not define in your experiment.

\*If using Spack as your Benchpark package manager

::

    . workspace/setup.sh
    ramble --workspace-dir workspace/my-experiment/my-system/workspace workspace setup

5. Test Your Benchmark
======================

If built successfully, the ``ramble on`` command will submit your experiments (job
scripts that ramble has generated) to the scheduler. Runtime errors at this point are
likely source code issues.

::

    ramble --workspace-dir workspace/my-experiment/my-system/workspace on
