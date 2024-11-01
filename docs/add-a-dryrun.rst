
.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

====================
Adding a Dryrun
====================

If you are contributing a system or experiment to our code repository you must add a passing dryrun test to the ``.github/workflows/run.yml`` file before
your pull request will be merged. 

Recommended systems/experiments to use as tests:

* genericx86
* tioga
* saxpy
* amg2023

For example, if you are contributing a system called foo you would test it with existing Saxpy experiment, the hash ID will be generated for you during setup and output by benchpark:

.. code-block:: yaml

  - name: Dry run dynamic saxpy on dynamic foo
    run: |
      benchpark system init --dest=foo-system foo
      benchpark experiment init --dest=saxpy-openmp saxpy
      benchpark setup ./saxpy ./foo-system workspace/
      . workspace/setup.sh
      ramble \
        --workspace-dir workspace/saxpy/foo-{hashID}/workspace \
        --disable-progress-bar \
        --disable-logger \
        workspace setup --dry-run


If you are contributing a benchmark and/or experiments to our code repository you can use an existing system to test your benchmark and experiments. 

For example, if you are contributing a new benchmark called bar:

.. code-block:: yaml

  - name: Dry run dynamic bar on dynamic genericx86
    run: |
      benchpark system init --dest=x86-system genericx86 
      benchpark experiment init --dest=bar-benchmark bar
      benchpark setup ./bar-benchmark ./x86-system workspace/
      . workspace/setup.sh
      ramble \
        --workspace-dir workspace/new-benchmark/genericx86-{hashID}/workspace \
        --disable-progress-bar \
        --disable-logger \
        workspace setup --dry-run