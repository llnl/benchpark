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

       repo/                     <- benchmarks are defined here
          **/application.py      <- ramble application spec
          **/package.py          <- spack package spec

       systems/                  <- system specs

************************
 Updating Documentation
************************

To build the documentation, requirements can be easily installed from
``.github/workflows/requirements/docs.txt``, using:

.. code-block:: bash

    pip install -r .github/workflows/requirements/docs.txt

This requires ``python>=3.11`` (or try an earlier version of sphinx). After updating the
documentation, render the pages with the following:

.. code-block:: bash

    cd docs
    make html

Then, open ``_build/html/index.html`` in a browser to view the rendered documentation.
