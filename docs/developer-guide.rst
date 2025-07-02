.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

===============
Developer Guide
===============

This guide is intended for people who want to work on Benchpark itself.

--------
Overview
--------

Benchpark is designed with several roles in mind:

#. **Users**, who want to install, run, and analyze performance of HPC benchmarks
#. **Application Developers**, who want to share their benchmarks.
#. **Procurement Teams**, who curate workload representation, evaluate and
   monitor system progress at HPC centers.
#. **HPC Vendors**, who understand the curated workload of HPC centers, propose
   systems.
#. **Benchpark Developers**, who work on Benchpark, add new features, and try
   to make the jobs of benchmark developers and users easier.

This gets us to the key concepts in Benchpark's software design:

- Specs: expressions for describing experiments and compute systems
- Packages: Python modules that build benchmarks according to a spec.

-------------------
Directory Structure
-------------------

So that you can familiarize yourself with the project, we will start with a
high-level view of Benchpark's directory structure:

.. code-block:: none

   benchpark/
      bin/
         benchpark              <- main benchpark executable

      common-resources/
         execute_experiment.tpl

      docs/                     <- source for this documentation

      experiments/              <- experiment specs are defined here

      lib/
         benchpark/             <- benchpark module
         scripts/               <- developer scripts

      modifiers/                <- modifier definitions

      repo/                     <- benchmarks are defined here

      systems/                  <- system specs are defined here

      var/
         exp_repo/
         sys_repo/

----------------------
Updating Documentation
----------------------

To update and build the documentation, we need to install the Sphinx package.

.. code-block:: bash

   pip install sphinx

After updating the documentation, render the pages with the following:

.. code-block:: bash

   cd docs
   make html

Then, open ``_build/html/index.html`` in a browser to view the rendered
documentation.
