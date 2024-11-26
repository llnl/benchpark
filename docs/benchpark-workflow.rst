.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

=================================
Benchpark Workflow
=================================

Follow the workflow diagram to determine if you can run existing configurations or if you will need to add or edit any Benchpark files. 

.. image:: /_static/images/workflow_fig.png


A. Run Existing Systems, Benchmarks and Experiments
----------------------------------------------------

If you are running on an existing ``system``, and the ``benchmark``
and ``experiment`` are already configured, you can proceed directly to the Running Benchpark Steps, 
starting with :doc:`benchpark-setup` for:

* Setup / Run / Analyze

B. System Specification
------------------------
A system specification defines the hardware, scheduling system, compilers, and any external libraries that might exist on a system. 

If you are running on a new system that has not been defined in Benchpark yet, proceed to :doc:`add-a-system-config` for the following:

* Find a similar ``system``

* Add or edit a ``system``


C. Benchmark Specification
---------------------------
A benchmark specification defines the application build and run behavior, utilizing spack for build and dependency management.

If you are creating a new benchmark that has not been defined in Benchpark yet, proceed to :doc:`add-a-benchmark` for the following: 

* Add a ``benchmark``


D. Experiment Specification
----------------------------
An experiment specification defines application parameters for experiments that require one or more application runs, such as single-node, scaling, or throughput runs.

If you are adding experiments to a new or existing benchmark, proceed to  :doc:`add-an-experiment` for the following: 

* Add/edit an ``experiment``


