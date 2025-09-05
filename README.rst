.. raw:: html

    <div align="left">
      <h2>
        <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/LLNL/benchpark/develop/docs/_static/images/benchpark-dark.svg" width="400">
        <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/LLNL/benchpark/develop/docs/_static/images/benchpark-light.svg" width="400">
        <img alt="Benchpark" src="https://raw.githubusercontent.com/LLNL/benchpark/develop/docs/_static/images/benchpark-light.svg" width="400">
        </picture>
      </h2>
    </div>

.. image:: https://codecov.io/gh/llnl/benchpark/branch/develop/graph/badge.svg?token=BKYKTSQ8DK
    :target: https://codecov.io/gh/llnl/benchpark

.. image:: https://github.com/llnl/benchpark/workflows/ci/badge.svg
    :target: https://github.com/LLNL/benchpark/actions/workflows/ci.yml

.. image:: https://github.com/llnl/benchpark/workflows/nightly/badge.svg
    :target: https://github.com/LLNL/benchpark/actions/workflows/nightly.yml

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/Dashboard-CDash-blue
    :target: https://my.cdash.org/index.php?project=Benchpark

Overview
--------
You can find detailed documentation at `software.llnl.gov/benchpark
<https://software.llnl.gov/benchpark>`_. Benchpark can also be found on `GitHub
<https://github.com/llnl/benchpark>`_.

Benchpark is an open collaborative repository for reproducible specifications of HPC benchmarks.
Benchpark enables cross-site collaboration on benchmarking by providing a mechanism for sharing
reproducible, working specifications for the following:

1. **System Specifications** (benchmark and experiment agnostic)

* Hardware information
* System software environment information (available compilers, MPI)
* Scheduler and launcher

2. **Benchmark Specifications** (system and experiment agnostic)

* Source repo and version
* Build configuration (with `Spack <https://github.com/spack/spack>`_)
* Run configuration (with `Ramble <https://github.com/GoogleCloudPlatform/ramble>`_)

3. **Experiment Specifications** (specific benchmark experiment on a system specification)

* Programming model (e.g., OpenMP, CUDA, ROCm) for the benchmark on a given system
* Parameters for individual runs in a study

Dependencies
------------
Benchpark uses the following open source projects for specifying configurations:

* `Spack <https://github.com/spack/spack>`_ for building benchmark and dependencies
* `Ramble <https://github.com/GoogleCloudPlatform/ramble>`_ for run configurations

Community
---------
Benchpark is an open source project.  Questions, discussion,and contributions of
new specifications as well as updates and improvements to existing specifications are welcome.

* `Adding a System Specification <https://software.llnl.gov/benchpark/add-a-system-config.html>`_
* `Adding a Benchmark Specification <https://software.llnl.gov/benchpark/add-a-benchmark.html>`_
* `Adding an Experiment Specification <https://software.llnl.gov/benchpark/add-an-experiment.html>`_

We use `github discussions <https://github.com/llnl/benchpark/discussions>`_ for Q&A and discussion.

Contributing
------------
To contribute to Benchpark, please open a `pull request
<https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests>`_
to the `develop` branch.  Your PR must pass Benchpark's unit tests, and must be `PEP 8 <https://peps.python.org/pep-0008/>`_ compliant.

Authors and citations
---------------------
Many thanks to Benchpark's `contributors <https://github.com/llnl/benchpark/graphs/contributors>`_.

Benchpark was created by Olga Pearce, Alec Scott, Greg Becker, Riyaz Haque, and Nathan Hanford.

To cite Benchpark, please use the following citation:

Olga Pearce, Alec Scott, Gregory Becker, Riyaz Haque, Nathan Hanford, Stephanie Brink,
Doug Jacobsen, Heidi Poxon, Jens Domke, and Todd Gamblin. 2023.
Towards Collaborative Continuous Benchmarking for HPC.
In Workshops of The International Conference on High Performance Computing,
Network, Storage, and Analysis (SC-W 2023), November 12–17, 2023, Denver, CO, USA.
ACM, New York, NY, USA, 9 pages.
`doi.org/10.1145/3624062.3624135 <https://doi.org/10.1145/3624062.3624135>`_.

Olga Pearce, Gregory Becker, Stephanie Brink, Nathan Hanford, Dewi Yokelson, August Knox, and Barry Rountree.
2025. HPC Benchmarking: Repeat, Replicate, Reproduce.
ACM Conference on Reproducibility and Replicability, July 29-31, Vancouver, Canada.

License
-------
Benchpark is released under the Apache 2.0 w/ LLVM Exception license. For more details see
the `LICENSE <https://github.com/LLNL/benchpark/blob/develop/LICENSE>`_ file.

LLNL-CODE-850629
