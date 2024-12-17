.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

=====================
Adding a System
=====================

This guide is intended for those wanting to run a benchmark on a new system,
such as vendors, system administrators, or application developers. It assumes
a system specification does not already exist.

System specifications include details like:

- How many CPUs are there per node on the system
- What pre-installed MPI/GPU libraries are available

A system description is a ``system.py`` file, where Benchpark provides the API
where you can represent a systems as an object and customize the description with command line arguments.

------------------------------
Identifying a Similar System
------------------------------

The easiest place to start when configuring a new system is to find the closest similar
one that has an existing configuration already. Existing system configurations are listed
in the table in :doc:`system-list`.

If you are running on a system with an accelerator, find an existing system with the same accelerator vendor,
and then secondarily, if you can, match the actual accererator.

1. accelerator.vendor
2. accelerator.name

Once you have found an existing system with a similar accelerator or if you do not have an accelerator,
match the following processor specs as closely as you can.

1. processor.name
2. processor.ISA
3. processor.uArch

For example, if your system has an NVIDIA A100 GPU and an Intel x86 Icelake CPUs, a similar config would share the A100 GPU, and CPU architecture may or may not match.
Or, if I do not have GPUs and instead have SapphireRapids CPUs, the closest match would be another system with x86_64, Xeon Platinum, SapphireRapids.

If there is not an exact match that is okay, steps for customizing are provided below.

-------------------------------------------------
Editing an Existing System to Match
-------------------------------------------------

.. note:
  make all these x86 example. Automate the directory structure?

If you want to add support for a new system you can add a class definition
for that system in a separate directory in ``systems/``.
The best way is to copy the system.py for the most similar system identified above, and then paste it in a new directory and update it.
For example the genericx86 system is defined in::

  $benchpark
  ├── systems
     ├── genericx86
        ├── system.py


The System base class defined in ``/lib/benchpark/system.py`` is shown below, some or all of the functions can be overridden to define custom system behavior.

.. literalinclude:: ../lib/benchpark/system.py
   :language: python

The main driver for configuring a system is done by defining a subclass for that system in a ``systems/{SYSTEM}/system.py`` file, which inherits from the System base class.

As is, the generic_x86 system subclass should run on most x86_64 systems, but we mostly provide it as a starting point for modifying or testing.
Potential common changes might be to edit the scheduler or number of cores per node, adding a GPU configuration, or adding other external compilers or packages.

To make these changes, we provided an example below, where we start with the generic_x86 system.py, and make a system called Modifiedx86.

1. First, make a copy of the system.py file in generic_x86 folder and move it into a new folder, e.g., ``systems/modified_x86/system.py``.
Then, update the class name to ``Modifiedx86``.::

    class Modifiedx86(System):

2. Next, to match our new system, we change the scheduler to slurm and the number of cores per node to 48, and number of GPUs per node to 2.::

    # this sets basic attributes of our system
    def initialize(self):
        super().initialize()
        self.scheduler = "slurm"
        self.sys_cores_per_node = "48"
        self.sys_gpus_per_node = "2"

3. Let's say the new system's GPUs are NVIDIA, we can add a variant that allows us to specify the version of CUDA we want to use, and the location of those CUDA installations on our system.
We then add the spack package configuration for our CUDA installations into the ``systems/modified_x86/externals/cuda`` directory (examples in Siera and Tioga systems).
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
    def external_pkg_configs(self):
        externals = Modifiedx86.resource_location / "externals"

        cuda_ver = self.spec.variants["cuda"][0]

        selections = []
        if cuda_ver == "10-1-243":
            selections.append(externals / "cuda" / "00-version-10-1-243-packages.yaml")
        elif cuda_ver == "11-8-0":
            selections.append(externals / "cuda" / "01-version-11-8-0-packages.yaml")

        return selections

Note, if your externals are *not* installed via Spack, read `Spack documentation on modules <https://spack.readthedocs.io/en/latest/packages_yaml.html#external-packages>`_.

4. Next, add any of the packages that can be managed by spack, such as blas/cublas pointing to the correct version,
this will generate the software configurations for spack (``software.yaml``). The actual version will be rendered by Ramble when it is built.
::
  def sw_description(self):
        return """\
  software:
    packages:
      default-compiler:
        pkg_spec: gcc
      compiler-gcc:
        pkg_spec: gcc
      default-mpi:
        pkg_spec: openmpi
      blas:
        pkg_spec: cublas@{default_cuda_version}
      cublas-cuda:
        pkg_spec: cublas@{default_cuda_version}
  """

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

        def initialize(self):
            super().initialize()

            self.scheduler = "slurm"
            setattr(self, "sys_cores_per_node", 48)
            self.sys_gpus_per_node = "2"

        def generate_description(self, output_dir):
            super().generate_description(output_dir)

            sw_description = pathlib.Path(output_dir) / "software.yaml"

            with open(sw_description, "w") as f:
                f.write(self.sw_description())

        def system_specific_variables(self):
            return {"cuda_arch": "70"}

        def external_pkg_configs(self):
            externals = Modifiedx86.resource_location / "externals"

            cuda_ver = self.spec.variants["cuda"][0]

            selections = []
            if cuda_ver == "10-1-243":
                selections.append(externals / "cuda" / "00-version-10-1-243-packages.yaml")
            elif cuda_ver == "11-8-0":
                selections.append(externals / "cuda" / "01-version-11-8-0-packages.yaml")

            return selections

        def sw_description(self):
            """This is somewhat vestigial, and maybe deleted later. The experiments
            will fail if these variables are not defined though, so for now
            they are still generated (but with more-generic values).
            """
            return """\
      software:
        packages:
          default-compiler:
            pkg_spec: gcc
          compiler-gcc:
            pkg_spec: gcc
          default-mpi:
            pkg_spec: openmpi
          blas:
            pkg_spec: cublas@{default_cuda_version}
          cublas-cuda:
            pkg_spec: cublas@{default_cuda_version}
    """

Once the modified system subclass is written, run:
``benchpark system init --dest=modifiedx86-system modifiedx86``

This will generate the required yaml configurations for your system and you can validate it works with a static experiment test.

------------------------
Validating the System
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
    max_request: "1000"  # n_ranks/n_nodes cannot exceed this
    n_ranks: '1000001'  # placeholder value
    n_nodes: '1000001'  # placeholder value
    batch_submit: "placeholder"
    mpi_command: "placeholder"


Once you can run an experiment successfully, and the yaml looks correct the new system has been validated and you can continue your :doc:`benchpark-workflow`.
