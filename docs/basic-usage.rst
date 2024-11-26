.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

===========
Basic Usage
===========

------------------
Benchpark Commands
------------------

The easiest way to get started is to run existing experiments one existing systems, or 
to modify one that is similar. You can search through the existing experiments and benchmarks with the below commands. 

Search for available system and experiment specifications in Benchpark.

.. list-table:: Searching for specifications in Benchpark
   :widths: 25 25 50
   :header-rows: 1

   * - Command
     - Description
     - Listing in the docs
   * - benchpark list
     - Lists all benchmarks and systems specified in Benchpark
     -
   * - benchpark list systems
     - Lists all system specified in Benchpark
     - :doc:`system-list`
   * - benchmark list benchmarks
     - Lists all benchmarks specified in Benchpark
     -
   * - benchpark tags workspace
     - Lists all tags specified in Benchpark
     -
   * - benchpark tags -a application workspace
     - Lists all tags specified for a given application in Benchpark
     -
   * - benchpark tags -t tag workspace
     - Lists all experiments in Benchpark with a given tag
     -

Now that you know the existing benchmarks and systems, you can determine your necessary workflow in :doc:`benchpark-workflow`.

------------
Getting Help
------------

Benchpark help menu::

    $ benchpark --help

.. program-output:: ../bin/benchpark --help
