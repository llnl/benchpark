.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

=====================
Adding a System
=====================

This guide is intended for those wanting to run a benchmark on a new system,
such as vendors, system administrators, or application developers. It assumes
a system specification does not already exist.

System specifications include two types of information:

1. Hardware specs in `hardware_description.yaml` (e.g., how many CPU cores the node has)
2. Software stack specs in `system.py` (e.g., installed compilers and libraries, along with their locations and versions)

.. note:
  Please replace the steps below with a flow diagram.

To specify a new system:

1. Identify a system in Benchpark with the same hardware.
2. If a system with the same hardware does not exist, add a new hardware description, as described in Adding System Hardware Specs section.
3. Identify the same software stack description.  Typically if the same hardware is already used by Benchpark, the same software stack may already be specified if the same vendor software stack is used on this hardware - or, if a software stack of your datacenter is already specified.
4. If the same software stack description does not exist, determine if there is one that can be parameterized to match yours.
5. If can't parameterize existing software description, add a new one.

-------------------------------
1. Adding System Hardware Specs
-------------------------------

We list hardware descriptions of Systems specified in Benchpark
in the System Catalogue in :doc:`system-list`.

If you are running on a system with an accelerator, find an existing system with the same accelerator vendor,
and then secondarily, if you can, match the actual accelerator.

1. accelerator.vendor
2. accelerator.name

Once you have found an existing system with a similar accelerator or if you do not have an accelerator,
match the following processor specs as closely as you can.

1. processor.name
2. processor.ISA
3. processor.uArch

For example, if your system has an NVIDIA A100 GPU and an Intel x86 Icelake CPUs,
a similar config would share the A100 GPU, and CPU architecture may or may not match.
Or, if I do not have GPUs and instead have SapphireRapids CPUs, the closest match
would be another system with x86_64, Xeon Platinum, SapphireRapids.

If there is not an exact match, you may add a new directory in the
`systems/all_hardware_descriptions/system_name` where `system_name` follows the naming convention::

  [INTEGRATOR]-MICROARCHITECTURE[-GPU][-NETWORK]

where::

  INTEGRATOR = COMPANY[_PRODUCTNAME][...]

  MICROARCHITECTURE = CPU Microarchitecture

  GPU = GPU Product Name

  NETWORK = Network Product Name

In the `systems/all_hardware_descriptions/system_name` directory, add a `hardware_description.yaml`
which follows the yaml format of existing `hardware_description.yaml` files.

-------------------------------------------------
2. Adding or Parameterizing System Software Stack
-------------------------------------------------
``system.py`` in Benchpark provides an API to represent a
system software stack as a command line parameterizable object.
If none of the available software stack specifications match your system,
you may add a `new-system` directory in the `systems` directory
where the `new-system` directory name follows the naming convention::

  SITE-SYSTEMNAME

where::

  SITE = nosite | abbreviated datacenter name

  SYSTEMNAME = the name of the specific system


.. note:
  make all these x86 example. Automate the directory structure?

Next, copy the system.py from the system with the most similar software stack
into `new-system` directory, and update it to match your system.
For example, the generic-x86 system software stack is defined in::

  $benchpark
  ├── systems
     ├── generic-x86
        ├── system.py


The System base class is defined in ``/lib/benchpark/system.py``, 
some or all of the functions can be overridden to define custom system behavior.
Your ``systems/{SYSTEM}/system.py`` should inherit from the System base class.

The generic-x86 system subclass should run on most x86_64 systems,
but we mostly provide it as a starting point for modifying or testing.
Potential common changes might be to edit the scheduler or number of cores per node,
adding a GPU configuration, or adding other external compilers or packages.

To make these changes, we provided an example below, where we start with the generic-x86
system.py, and make a system called Modifiedx86.

1. First, make a copy of the system.py file in generic_x86 folder and move it into a new folder,
   e.g., ``systems/modified_x86/system.py``.  Then, update the class name to ``Modifiedx86``.::

    class Modifiedx86(System):

2. Next, to match our new system, we change the scheduler to slurm and the number of
   cores per node to 48, and number of GPUs per node to 2.::

    # this sets basic attributes of our system
    def __init__(self, spec):
        super().__init__(spec)
        self.scheduler = "slurm"
        self.sys_cores_per_node = "48"
        self.sys_gpus_per_node = "2"

3. Let's say the new system's GPUs are NVIDIA, we can add a variant that allows us to specify
   the version of CUDA we want to use, and the location of those CUDA installations on our system.
   We then add the spack package configuration for our CUDA installations into the `compute_packages_section`.
::

    # import the variant feature at the top of your system.py
    from benchpark.directives import variant

    # this allows us to specify which cuda version we want as a command line parameter
    variant(
        "cuda",
        default="11-8-0",
        values=("11-8-0", "10-1-243"),
        description="CUDA version",
    )

    # set this to pass to spack
    def system_specific_variables(self):
        return {"cuda_arch": "70"}

    # define the external package locations
    def compute_packages_section(self):
        selections = {
            "packages": {
                "elfutils": {
                    "externals": [{"spec": "elfutils@0.176", "prefix": "/usr"}],
                    "buildable": False,
                },
                "papi": {
                    "buildable": False,
                    "externals": [{"spec": "papi@5.2.0.0", "prefix": "/usr"}],
                },
            }
        }
        if self.spec.satisfies("cuda=10-1-243"):
            selections["packages"] |= {
                "cusparse": {
                    "externals": [
                        {
                            "spec": "cusparse@10.1.243",
                            "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                        }
                    ],
                    "buildable": False,
                },
                "cuda": {
                    "externals": [
                        {
                            "spec": "cuda@10.1.243+allow-unsupported-compilers",
                            "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                        }
                    ],
                    "buildable": False,
                },
            }
        elif self.spec.satisfies("cuda=11-8-0"):
            selections["packages"] |= {
                "cusparse": {
                    "externals": [
                        {
                            "spec": "cusparse@11.8.0",
                            "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                        }
                    ],
                    "buildable": False,
                },
                "cuda": {
                    "externals": [
                        {
                            "spec": "cuda@11.8.0+allow-unsupported-compilers",
                            "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                        }
                    ],
                    "buildable": False,
                },
            }

        return selections

External packages can be found via `benchpark system external ---new-system {mysite}-{mysystem}`.
Note, if your externals are *not* installed via Spack, read `Spack documentation on modules <https://spack.readthedocs.io/en/latest/packages_yaml.html#external-packages>`_.

4. Next, add any of the packages that can be managed by spack, such as blas/cublas pointing to the correct version,
this will generate the software configurations for spack (``software.yaml``). The actual version will be rendered by Ramble when it is built.
::
  def compute_software_section(self):
    return {
        "software": {
            "packages": {
                "default-compiler": {"pkg_spec": "gcc"},
                "compiler-gcc": {"pkg_spec": "gcc"},
                "default-mpi": {"pkg_spec": "openmpi"},
                "blas": {"pkg_spec": "openblas"},
                "lapack": {"pkg_spec": "openblas"},
            }
        }
    }

5. The full system.py class for the modified_x86 system should now look like:
::
    import pathlib

    from benchpark.directives import variant
    from benchpark.system import System

    class Modifiedx86(System):

        variant(
            "cuda",
            default="11-8-0",
            values=("11-8-0", "10-1-243"),
            description="CUDA version",
        )

        def __init__(self):
            super().__init__()

            self.scheduler = "slurm"
            setattr(self, "sys_cores_per_node", 48)
            self.sys_gpus_per_node = "2"

        def system_specific_variables(self):
            return {"cuda_arch": "70"}

        def compute_packages_section(self):
          selections = {
              "packages": {
                  "elfutils": {
                      "externals": [{"spec": "elfutils@0.176", "prefix": "/usr"}],
                      "buildable": False,
                  },
                  "papi": {
                      "buildable": False,
                      "externals": [{"spec": "papi@5.2.0.0", "prefix": "/usr"}],
                  },
              }
          }
          if self.spec.satisfies("cuda=10-1-243"):
              selections["packages"] |= {
                  "cusparse": {
                      "externals": [
                          {
                              "spec": "cusparse@10.1.243",
                              "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                          }
                      ],
                      "buildable": False,
                  },
                  "cuda": {
                      "externals": [
                          {
                              "spec": "cuda@10.1.243+allow-unsupported-compilers",
                              "prefix": "/usr/tce/packages/cuda/cuda-10.1.243",
                          }
                      ],
                      "buildable": False,
                  },
              }
          elif self.spec.satisfies("cuda=11-8-0"):
              selections["packages"] |= {
                  "cusparse": {
                      "externals": [
                          {
                              "spec": "cusparse@11.8.0",
                              "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                          }
                      ],
                      "buildable": False,
                  },
                  "cuda": {
                      "externals": [
                          {
                              "spec": "cuda@11.8.0+allow-unsupported-compilers",
                              "prefix": "/usr/tce/packages/cuda/cuda-11.8.0",
                          }
                      ],
                      "buildable": False,
                  },
              }

          return selections

        def compute_software_section(self):
          return {
              "software": {
                  "packages": {
                      "default-compiler": {"pkg_spec": "gcc"},
                      "compiler-gcc": {"pkg_spec": "gcc"},
                      "default-mpi": {"pkg_spec": "openmpi"},
                      "blas": {"pkg_spec": "openblas"},
                      "lapack": {"pkg_spec": "openblas"},
                  }
              }
          }
    """

Once the modified system subclass is written, run:
``benchpark system init --dest=modifiedx86-system modifiedx86``

This will generate the required yaml configurations for your system and you can validate it works with a static experiment test.

.. Note::

  Use the ``benchpark info system {system_name}`` to find additional variants that are available to all systems.
  This includes settings such as: the job timeout, submitting to a different partition/queue, and setting the account/bank.


------------------------
3. Validating the System
------------------------

To manually validate your new system, you should initialize it and run an existing experiment such as saxpy. For example::

  benchpark system init --dest=modifiedx86-system modifiedx86
  benchpark experiment init --dest=saxpy saxpy +openmp
  benchpark setup ./saxpy ./modifiedx86-system workspace/

Then you can run the commands provided by the output, the experiments should be built and run successfully without any errors.

The following yaml files are examples of what is generated for the modified_x86 system from the example after it is initialized:

1. ``system_id.yaml`` describes the system hardware, including the integrator (and the name of the product node or cluster type), the processor, (optionally) the accelerator, and the network; the information included here is what you will typically see recorded about the system on Top500.org.  We intend to make the system definitions in Benchpark searchable, and will add a schema to enforce consistency; until then, please copy the file and fill out all of the fields without changing the keys.  Also listed is the specific system the config was developed and tested on, as well as the known systems with the same hardware so that the users of those systems can find this system specification.

.. code-block:: yaml

  system:
    name: Modifiedx86
    spec: sysbuiltin.modifiedx86 cuda=11-8-0
    config-hash: 5310ebe8b2c841108e5da854c75dab931f5397a7fb41726902bb8a51ffb84a36


2. ``software.yaml`` defines default compiler and package names your package
manager (Spack) should use to build the benchmarks on this system.
``software.yaml`` becomes the spack section in the `Ramble configuration
file
<https://ramble.readthedocs.io/en/latest/configuration_files.html#external-spack-environment-support>`_.

.. code-block:: yaml

    software:
      packages:
        default-compiler:
          pkg_spec: 'gcc'
        compiler-gcc:
          pkg_spec: 'gcc'
        default-mpi:
          pkg_spec: 'openmpi'
        blas:
          pkg_spec: cublas@{default_cuda_version}
        cublas-cuda:
          pkg_spec: cublas@{default_cuda_version}

3. ``variables.yaml`` defines system-specific launcher and job scheduler.

.. code-block:: yaml

  variables:
    timeout: "120"
    scheduler: "slurm"
    sys_cores_per_node: "48"
    sys_gpus_per_node: 2
    cuda_arch: 70
    n_ranks: 18446744073709551615  # placeholder value
    n_nodes: 18446744073709551615  # placeholder value
    batch_submit: "placeholder"
    mpi_command: "placeholder"


Once you can run an experiment successfully, and the yaml looks correct, the new system has been validated and you can continue your :doc:`benchpark-workflow`.
