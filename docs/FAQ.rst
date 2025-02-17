.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0


==========================
Frequently Asked Questions
==========================

---------------------------------
Benchmark not yet in Spack/Ramble
---------------------------------

By default, Benchpark will use ${Benchmark1} specifications (``package.py`` and ``application.py``)
provided in the Spack and Ramble repos.
It is possible to overwrite the benchmark specifications provided in the Spack and Ramble repos.
To do so, add ``package.py`` and/or ``application.py`` for ${Benchmark1} in
``benchpark/repo/${Benchmark1}``::

  benchpark
  └── repo
     ├── ${Benchmark1}
     │  ├── application.py
     │  └── package.py
     └── repo.yaml

``benchpark/repo`` can be used as a staging area for the build and run specification for
${Benchmark1} so that you can test them together with your experiment specification
on a given system.  Once the experiment is working and merged into the develop branch of Benchpark,
we would like to encourage the contributors to upstream the ``package.py`` to Spack,
and the ``application.py`` to Ramble.  When those PRs are approved and merged,
please submit a PR to remove the duplicated specification from ``benchpark/repo``.

----------------------------------
Spack/Ramble versions in Benchpark
----------------------------------

Benchpark depends on the build functionality provided in
`Spack <https://github.com/spack/spack>`_,
and run functionality provided in
`Ramble <https://github.com/GoogleCloudPlatform/ramble>`_.
To allow for testing before pulling in updates in Spack and Ramble,
Benchpark clones and uses the versions of Spack and Ramble
specified in ``checkout-versions.yaml``.

The user might notice this delay in Spack and Ramble versions
in two ways:

* The latest functionality of Spack and/or Ramble may not yet be
  available in Benchpark.
* The latest package.py specifications available in Spack
  and application.py specifications available in Ramble
  may not be available in Benchpark.

At your own risk, you may go into the cloned Spack and Ramble
directories and perform a git pull to grab those updates.
This may be useful for package updates, but perilous for
functionality updates.

Alternatively, the user may temporarily copy the needed packages
into ``benchpark/repo``, and remove them when Benchpark updates
to the next version of Spack/Ramble.

-------------------------
What to rerun after edits
-------------------------

.. list-table:: I made changes.  What should I rerun?
   :widths: 35 65
   :header-rows: 1

   * - What I changed
     - Commands to rerun
   * - configs
     - ``ramble --disable-progress-bar --workspace-dir . workspace setup``
   * - benchmark's package.py
     - ``ramble --disable-progress-bar --workspace-dir . workspace setup``
   * - dependency of package.py
     - ``ramble --disable-progress-bar --workspace-dir . workspace setup``
   * - experiment parameters
     - delete ``workspace/experiments``
   * - wish to rerun experiments
     - delete ``workspace/experiments``
