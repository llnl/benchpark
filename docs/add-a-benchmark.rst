.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

==================
Adding a Benchmark
==================

This guide is intended for application developers who want to add a benchmark so that it can be run with Benchpark.

Create a New Benchmark
------------------------

The following system-independent specification is required for each ${Benchmark1} in ``benchpark/repo/${Benchmark1}``:

- ``package.py`` is a Spack specification that defines how to build and install ${Benchmark1}.
- ``application.py`` is a Ramble specification that defines the ${Benchmark1} input and parameters.

During ``benchpark setup`` the user selects ${Benchmark1} to run as the following::

     benchpark setup </output/path/to/experiments_root> </output/path/to/system_root> </output/path/to/workspace> 

By default, Benchpark will use ${Benchmark1} specifications (``application.py`` and ``package.py``)
provided in the Spack and Ramble repos.
It is possible to overwrite the benchmark specifications provided in the Spack and Ramble repos;
see :doc:`FAQ` for details.


Validate a Benchmark 
------------------------

Now that the benchmark has been created/updated you need to configure at least one experiment, and then validate it, see :doc:`add-an-experiment`.
