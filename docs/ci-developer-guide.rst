..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

####################
 CI Developer Guide
####################

This guide is intended for people who want to modify the GitHub/Gitlab CI for benchpark

********
 GitLab
********

The Benchpark GitLab tests run on LC systems as a part of the
``https://lc.llnl.gov/gitlab``. The goal is to build and run the benchmarks on systems
with different programming models, as well as test the functionality of the benchpark
library. GitLab configuration files are located under the ``.gitlab`` folder and
specified by the ``.gitlab-ci.yml`` configuration file:

::

    .gitlab-ci.yml
    .gitlab/
       bin/
       tests/
       utils/

1. ``.gitlab-ci.yml`` defines project-wide variables, the job stage pipeline, and
   different sets of tests (e.g. nightly, daily). This file also includes some
   pre-defined utility functions from the `LLNL/radiuss-shared-ci project
   <https://github.com/LLNL/radiuss-shared-ci>`_.
2. ``.gitlab/bin/`` stores "binaries" that are used during CI execution.

.. figure:: _static/images/shared-nonshared.png
    :align: left
    :alt: Slide Preview

    Fig. 1: Running experiments using a "non-shared" strategy (A) versus a shared
    allocation strategy (B).

3. ``.gitlab/tests/`` Define the different types of tests. Add a benchmark to a given
   test by adding to the ``BENCHMARK`` list variable for the appropriate ``HOST`` and
   ``VARIANT``. Add tests for a system by defining a new group to the list defined under
   the appropriate ``parallel:matrix:``. The ``HOST`` must have existing runners on the
   ``https://lc.llnl.gov/gitlab`` (managed by admins) in order to actually execute. All
   available LC instance runners can be found `here
   <https://lc.llnl.gov/gitlab/benchpark/benchpark/-/settings/ci_cd#js-runners-settings>`_.

   a. Nightly tests (``nightly.yml``) defines all of the tests that run nightly. All of
      the tests for all experiments and systems are defined in this file. Tests are ran
      sequentially on a given system, but are parallelized across the systems
      (non-shared Figure 1A). The main goal for the nightly tests is to test all
      available programming models for as many of the benchmarks in benchpark as
      possible, which we post the successes/failures on the develop branch to our `CDash
      dashboard <https://my.cdash.org/index.php?project=Benchpark>`_. An experiment
      failing on the dashboard should indicate that this experiment should also fail if
      you try building and running yourself.
   b. Daily tests are split into multiple categories

      i. Non-shared tests (non-shared Figure 1A) ``non_shared.yml`` operate the same way
         as the nightly tests and run sequentially.
      ii. Shared Flux tests (shared Figure 1B) ``shared_flux_clusters.yml`` has all of
          the tests that we execute on clusters running system-wide flux. The testing
          strategy allocates a single node and then submits all of the tests to that
          single node. This strategy avoids the time spent waiting for an allocation
          between tests.
      iii. Shared Slurm tests (shared Figure 1B) ``shared_slurm_clusters.yml`` has all
           of the tests that we execute on clusters running system-wide flux. The
           strategy for these clusters is similar to the flux clusters, but first
           involves starting flux on the allocated node, which is necessary since
           testing the benchpark workflow involves submitting a job within a job step in
           this case, which is not possible using slurm.

4. ``.gitlab/utils/`` contains various utility functions for:

   a. Checking machine status ``machine_checks.yml``
   b. Cancelling jobs ``cancel-flux.sh`` and ``cancel-slurm.sh``
   c. Defining common rules ``rules.yml``
   d. A reproducible script for executing an experiment in benchpark
      ``run-experiment.sh``
   e. Reporting GitLab status to GitHub PRs ``status.yml``.

********
 GitHub
********

Although the GitLab tests cover the most critical step (building and running the
benchmarks across multiple LC systems) they do not test all of the benchmarks/systems or
library functionality in benchpark. The GitHub tests use the GitHub virtual machine
runners to test mostly python functionality, which is platform independent. The
following is a description of the different types of GitHub testing:

run.yml
=======

Dryruns
-------

Dryruns can be thought of similarly to the GitLab tests, but only involve testing up to
the ``ramble workspace setup`` step with the ``--dry-run`` flag, which sets up the
ramble workspace, but does not build the benchmark. The dryruns are automatically
enumerated using the output from the ``benchpark list`` command, which is used to list
experiments for all programming models and scaling options, as well as enumerating the
modifiers. For each programming model that a benchmark implements, a dryrun will be
executed on every system in benchpark that contains that programming model in
``self.programming_models``.

- ``.github/utils/dryruns.py`` contains the main script that enumerates all of the
  dryruns cases, and executes them in a ``subprocess`` call.
- ``.github/utils/dryrun.sh`` executes a single dryrun, provided a ``benchmark_spec``
  and ``system_spec``.
- ``.github/workflows/run.yml`` defines the ``dryrunexperiments`` job, that will be
  executed by a GitHub runner. Runs are separated by programming model, scaling type,
  and modifiers, and are executed in parallel.

Dryruns are mainly for verifying that a given experiment/system is able to be
initialized based on the programming models and scaling types have been included in the
experiment class. Simple errors such as syntax errors will be caught by the linter
instead. While much of the testing covered by dryruns is likely redundant, they are
relatively inexpensive to run.

Saxpy
-----

There is a singular job that builds and runs the ``saxpy`` experiment on a GitHub
virtual machine runner. This step additionally tests ramble workspace analyze & archive,
uploading the binary as a CI cache, and the benchpark functionality to run a pre-built
binary (reusing the spack-built binary).

Pytest
------

The Pytest unit tests are designed to cover as many different cases of the benchpark
library as possible, useful for checking Python object properties that cannot be checked
from the command line. Additionally, we can easily check that certain errors are raised
under specific conditions to ensure our error checking is working properly. Notice that
our Pytest coverage is not comprehensive on its own, since we have other testing, i.e.
GitLab and GitHub (dryruns), that covers many cases.

style.yml - Lint
================

The linter step checks:

- Check Python code formatting using ``black``
      - Fix black linter errors using ``python -m black dir/filename.py`` or
            ``python -m black .`` (in source code dir).
- Check spelling using ``codespell``
      - Fix the spelling errors manually.
- Sort imports using ``isort``
      - Fix isort linter errors using ``isort .``
- ``flake8`` for checking Python style enforcement
      - Fix flake linter errors manually
- ``yamlfix`` for formatting ``.yaml``/``.yml`` files
      - Fix yaml linter errors using ``yamlfix dir.filename.yaml``
- ``docstrfmt`` for formatting ``.rst`` files
      - Fix docs linter errors using ``docstrfmt -p
        .github/workflows/requirements/docstrfmt.toml docs/``

Code Coverage
=============

`Code coverage <https://about.codecov.io/>`_ measures the amount of lines that are
"covered" by a given test, i.e. if a line was executed it counts as coverage. Code
coverage should automatically report on all open pull requests.

It is possible to run coverage for any test that uses ``bin/benchpark`` by providing
``BENCHPARK_RUN_COVERAGE=[YOUR_DIRNAME]`` and add an upload step which takes the
following form.:

::

    - name: Upload coverage to Codecov
       uses: codecov/codecov-action@v4
       with:
          token: ${{ secrets.BENCHPARK_CODECOV_TOKEN }}
          directory: ./coverage-data-$BENCHPARK_RUN_COVERAGE
          flags: dryrunexperiments-$BENCHPARK_RUN_COVERAGE
          verbose: true
          fail_ci_if_error: true

Additionally, for each upload step added, ``after_n_builds`` in ``codecov.yml`` needs to
be incremented by 1.

*******
 CDash
*******

The successes/failures of our GitLab tests are posted to our CDash dashboard `CDash
dashboard <https://my.cdash.org/index.php?project=Benchpark>`_. There is a dashboard for
the nightly tests on the develop branch, and several dashboards for each system for
daily PRs.

The following files are related to CDash:

1. ``CTestGitlab.cmake`` configures CTest variables, the dashboard names and runs the
   tests and submits the results.
2. ``CTestConfig.cmake`` sets the cdash token and configuration variables.
3. ``CMakeLists.txt`` enables CTest and adds the gitlab test.
4. ``.gitlab/utils/status.yml`` Contains the logic to run CTest after a test completes
   and upload the status to the Benchpark CDash dashboard.
