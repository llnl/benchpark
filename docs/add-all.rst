.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

.. _legacy-add-benchmark:
------------------
Adding a Benchmark
------------------

.. warning::
    This page provides legacy instructions for adding benchmarks, system
    specifications, and experiments in Benchpark. This process is expected to
    be deprecated in a future release.

The following system-independent specification is required for each ${Benchmark1}:

- ``package.py`` is a Spack specification that defines how to build and install ${Benchmark1}.
- ``application.py`` is a Ramble specification that defines the ${Benchmark1} input and parameters.

During ``benchpark setup`` the user selects ${Benchmark1} to run as the following::

     benchpark setup ${Benchmark1}/${ProgrammingModel1} ${System1} </output/path/to/experiments_root>

By default, Benchpark will use ${Benchmark1} specifications (``package.py`` and ``application.py``)
provided in the Spack and Ramble repos.
It is possible to overwrite the benchmark specifications provided in the Spack and Ramble repos;
see :doc:`FAQ-benchpark-repo` for details.

.. _legacy-add-system:
-----------------------------
Adding a System Specification
-----------------------------

.. warning::
    This page provides legacy instructions for adding benchmarks, system
    specifications, and experiments in Benchpark. This process is expected to
    be deprecated in a future release.

System specifications include details like

- How many CPUs are there per node on the system
- What pre-installed MPI/GPU libraries are available

A system description is a set of YAML files collected into a directory.
You can generate these files directly, but Benchpark also provides an API
where you can represent systems as objects and customize their description
with command line arguments.

Using System API to Generate a System Description
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

System classes are defined in ``systems/``; once the class has been
defined, you can invoke ``benchpark system init`` to generate a system
configuration directory that can then be passed to ``benchpark setup``::

    benchpark system init --dest=tioga-system tioga rocm=551 compiler=cce ~gtl

where "tioga rocm=551 compiler=cce ~gtl" describes a config for Tioga that
uses ROCm 5.5.1 components, a CCE compiler, and MPI without GTL support.

If you want to add support for a new system you can add a class definition
for that system in a separate directory in ``/systems/``. For
example the Tioga system is defined in::

  $benchpark
  ├── systems
     ├── tioga
        ├── system.py

Static System Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``benchpark/legacy/systems`` contains a number of static, manually-generated system
definitions. As an alternative to implementing a new ``System`` class, you
can add a new directory with a name which identifies the system.

The naming convention for the systems is as following::

  SITE-[SYSTEMNAME-][INTEGRATOR]-MICROARCHITECTURE[-GPU][-NETWORK]

where::

  SITE = nosite | DATACENTERNAME

  SYSTEMNAME = the name of the specific system

  INTEGRATOR = COMPANY[_PRODUCTNAME][...]

  MICROARCHITECTURE = CPU Microarchitecture

  GPU = GPU Product Name

  NETWORK = Network Product Name

Benchpark has definitions for the following (nosite) systems:

- nosite-AWS_PCluster_Hpc7a-zen4-EFA

- nosite-HPECray-zen3-MI250X-Slingshot (same hardware as Frontier, Lumi, Tioga)

- nosite-x86_64 (x86 CPU only platform)



Benchpark has definitions for the following site-specific systems:

- LLNL-Magma-Penguin-icelake-OmniPath

- LLNL-Sierra-IBM-power9-V100-Infiniband (Sierra, Lassen)

- LLNL-Tioga-HPECray-zen3-MI250X-Slingshot


The following files are required for each nosite system ``benchpark/legacy/systems/${SYSTEM}``:

1. ``system_definition.yaml`` describes the system hardware, including the integrator (and the name of the product node or cluster type), the processor, (optionally) the accelerator, and the network; the information included here is what you will typically see recorded about the system on Top500.org.  We intend to make the system definitions in Benchpark searchable, and will add a schema to enforce consistency; until then, please copy the file and fill out all of the fields without changing the keys.  Also listed is the specific system the config was developed and tested on, as well as the known systems with the same hardware so that the users of those systems can find this system specification.

.. code-block:: yaml

  system_definition:
    name: HPECray-zen3-MI250X-Slingshot # or site-specific name, e.g., Frontier at ORNL
    site:
    system: HPECray-zen3-MI250X-Slingshot
    integrator:
      vendor: HPECray
      name: EX235a
    processor:
      vendor: AMD
      name: EPYC-Zen3
      ISA: x86_64
      uArch: zen3
    accelerator:
      vendor: AMD
      name: MI250X
      ISA: GCN
      uArch: gfx90a
    interconnect:
      vendor: HPECray
      name: Slingshot11
    system-tested:
      site: LLNL
      name: tioga
      installation-year: 2022
      description: [top500](https://www.top500.org/system/180052)
    top500-system-instances:
      - Frontier (ORNL)
      - Lumi     (CSC)
      - Tioga    (LLNL)


2. ``software.yaml`` defines default compiler and package names your package
manager (Spack) should use to build the benchmarks on this system.
``software.yaml`` becomes the spack section in the `Ramble configuration
file
<https://googlecloudplatform.github.io/ramble/configuration_files.html#spack-config>`_.

.. code-block:: yaml

    software:
      packages:
        default-compiler:
          pkg_spec: 'spack_spec_for_package'
        default-mpi:
          pkg_spec: 'spack_spec_for_package'

3. ``variables.yaml`` defines system-specific launcher and job scheduler.

.. code-block:: yaml

    variables:
      timeout: '30'
      scheduler: "slurm"
      sys_cores_per_node: "128"
      sys_gpus_per_node: "4"
      sys_mem_per_node unset
      max_request: "1000"  # n_ranks/n_nodes cannot exceed this
      n_ranks: '1000001'  # placeholder value
      n_nodes: '1000001'  # placeholder value
      batch_submit: "placeholder"
      mpi_command: "placeholder"
      # batch_queue: "pbatch"
      # batch_bank: "guest"

If defining a specific system, one can be more specific with available software versions
and packages, as demonstrated in :ref:`legacy-add-system`.

.. _legacy-add-experiment:
--------------------
Adding an Experiment
--------------------

.. warning::
    This page provides legacy instructions for adding benchmarks, system
    specifications, and experiments in Benchpark. This process is expected to
    be deprecated in a future release.

Experiment Specifications are located in ``benchpark/experiments``.
They are organized by the *ProgrammingModel* used for on-node parallelization for the experiment,
e.g., ``benchpark/experiments/amg2023/cuda`` for an AMG2023 experiment using CUDA (on an NVIDIA GPU),
and ``benchpark/experiments/amg2023/openmp`` for an AMG2023 experiment using OpenMP (on a CPU).
These files, in conjunction with the system configuration files and package/application repositories,
are used to generate a set of concrete Ramble experiments for the target system and programming model.

- ``ramble.yaml`` defines the `Ramble specs <https://googlecloudplatform.github.io/ramble/workspace_config.html#workspace-config>`_ for building, running, analyzing and archiving experiments.
- ``execution_template.tpl`` serves as a template for the final experiment script that will be concretized and executed.

A detailed description of Ramble configuration files is available at `Ramble workspace_config <https://googlecloudplatform.github.io/ramble/workspace_config.html>`_.
