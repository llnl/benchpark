..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#################
 Developer Guide
#################

This guide is intended for people who want to work on Benchpark itself.

**********
 Overview
**********

Benchpark is designed with several roles in mind:

1. **Users**, who want to install, run, and analyze performance of HPC benchmarks
2. **Application Developers**, who want to share their benchmarks.
3. **Procurement Teams**, who curate workload representation, evaluate and monitor
   system progress at HPC centers.
4. **HPC Vendors**, who understand the curated workload of HPC centers, propose systems.
5. **Benchpark Developers**, who work on Benchpark, add new features, and try to make
   the jobs of benchmark developers and users easier.

This gets us to the key concepts in Benchpark's software design:

- Specs: expressions for describing experiments and compute systems
- Packages: Python modules that build benchmarks according to a spec.

*********************
 Directory Structure
*********************

So that you can familiarize yourself with the project, we will start with a high-level
view of Benchpark's directory structure:

.. code-block:: none

    benchpark/
       bin/
          benchpark              <- main benchpark executable
          benchpark-python       <- execute python scripts using benchpark library

       docs/                     <- source for this documentation

       experiments/              <- experiment specs

       lib/
          benchpark/             <- benchpark library
          scripts/               <- scripts for common benchpark use cases

       modifiers/                <- modifier definitions

       repos/                    <- benchmarks are defined here
          **/application.py      <- ramble application spec
          **/package.py          <- spack package spec

       systems/                  <- system specs

******************************
 Updating Python Dependencies
******************************

Benchpark requires Python 3.8 or newer. Shared runtime and test dependencies live in
``requirements/benchpark.txt``. Add a lower bound only when Benchpark needs
functionality from that release, and keep a release compatible with Python 3.8 available
to pip. Otherwise, leave the requirement unpinned so pip can select a compatible
release.

Ramble's Python dependencies come from ``requirements.txt`` in its checkout, at the
commit selected by ``checkout-versions.yaml``. Bootstrap installs them into the Python
environment running Benchpark before importing Ramble. It checks installed versions on
each invocation so an existing checkout also works with a new virtual environment. There
is no separate copy of Ramble's requirements to maintain in Benchpark. ``benchpark
mirror`` downloads both Benchpark's requirements and the workspace Ramble checkout's
requirements for offline installation.

Documentation, style, and container requirements use exact pins for their respective
Python environments. Use environment markers when different Python versions need
different pins, as in ``requirements/docs.txt``. The dependency workflow installs shared
requirements, bootstraps Ramble, and installs the analyze extra on Python 3.8 and 3.13,
then runs ``pip check``.

Coverage tools live separately in ``requirements/coverage.txt``. Coverage measures which
lines and branches execute during tests; ``pytest-cov`` connects it to pytest. Jobs that
collect coverage use Python 3.13 and install this file explicitly, so these tools do not
raise the minimum Python version for user installations.

************************
 Updating Documentation
************************

To build the documentation, install the shared and documentation requirements:

.. code-block:: bash

    pip install -r requirements.txt -r requirements/docs.txt ".[analyze]"

This requires ``python>=3.11``. The documentation requirements select Sphinx 8.2.3 for
Python 3.11 or 3.12 and Sphinx 9.2.0 for Python 3.13 or newer. After updating the
documentation, render the pages with the following:

.. code-block:: bash

    cd docs
    make html

Then, open ``_build/html/index.html`` in a browser to view the rendered documentation.
