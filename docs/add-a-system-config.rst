..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

Adding a System
===============

This guide is intended for those who would like to add a new system to benchpark, such
as vendors, system administrators, or application developers. Benchpark provides an API
for representing system specifications as objects and options to customize the
specification on the command line. System specifications are defined in ``system.py``
files located in the systems directory: ``benchpark/systems/<system>/``.

..
    note:
    Please replace the steps below with a flow diagram.

To determine if you need to create a new system:

1. Identify a system in Benchpark with the same hardware. See :doc:`system-list` to see
   hardware descriptions for all available benchpark systems.
2. If a system with the same hardware does not exist, add a new hardware description, as
   described in :ref:`adding-system-hardware-specs`.
3. Identify the same software stack description. Typically if the same hardware is
   already used by Benchpark, the same software stack may already be specified if the
   same vendor software stack is used on this hardware - or, if a software stack of your
   datacenter is already specified. If a system exists with the same software stack, add
   your system to that ``system.py`` as a value under the ``cluster`` variant, and
   specify your systems specific resource configuration under the ``id_to_resources``
   dictionary.
4. If the same software stack description does not exist, determine if there is one that
   can be parameterized to match yours, otherwise proceed with adding a new system.

.. _adding-system-hardware-specs:

1. Adding System Hardware Specs
-------------------------------

We list hardware descriptions of Systems specified in Benchpark in the System Catalogue
in :doc:`system-list`.

If you are running on a system with an accelerator, find an existing system with the
same accelerator vendor, and then secondarily, if you can, match the actual accelerator.

1. accelerator.vendor
2. accelerator.name
3. accelerator.ISA
4. accelerator.uArch

Once you have found an existing system with a similar accelerator or if you do not have
an accelerator, match the following processor specs as closely as you can.

1. processor.name
2. processor.ISA
3. processor.uArch
4. processor.vendor

And add the interconnect vendor and product name.

1. interconnect.vendor
2. interconnect.name

For example, if your system has an NVIDIA A100 GPU and an Intel x86 Icelake CPUs, a
similar config would share the A100 GPU, and CPU architecture may or may not match. Or,
if I do not have GPUs and instead have SapphireRapids CPUs, the closest match would be
another system with x86_64, Xeon Platinum, SapphireRapids.

If there is not an exact match, you may add a new directory in the
`systems/all_hardware_descriptions/system_name` where `system_name` follows the naming
convention:

::

    [INTEGRATOR]-MICROARCHITECTURE[-GPU][-NETWORK]

where:

::

    INTEGRATOR = COMPANY[_PRODUCTNAME][...]

    MICROARCHITECTURE = CPU Microarchitecture

    GPU = GPU Product Name

    NETWORK = Network Product Name

In the `systems/all_hardware_descriptions/system_name` directory, add a
`hardware_description.yaml` which follows the yaml format of existing
`hardware_description.yaml` files.

1. Creating the System class
-------------------------------------------------

In this example, we will recreate the AWS ``system.py`` that we use for benchpark tutorials. At minimum, we import the base benchpark ``System`` class, which our ``AwsTutorial`` system will inherit from. We also import the maintainer and variant directives, which provide the utilities to track a maintainer by their GitHub username and variants to specify configurable properties of our system. We use ``instance_type`` instead of ``cluster`` (you will see ``cluster`` in other systems), because ``instance_type`` is more fitting in the context of AWS.

We configure the 

::

    from benchpark.directives import maintainers, variant
    from benchpark.paths import hardware_descriptions
    from benchpark.system import System


    class AwsTutorial(System):
        maintainers("michaelmckinsey1")

        id_to_resources = {
            "c7i.12xlarge": {
                "system_site": "aws",
                "sys_cores_per_node": 48,
                "sys_mem_per_node_GB": 96,
                "hardware_key": str(hardware_descriptions)
                + "/AWS_Tutorial-sapphirerapids-EFA/hardware_description.yaml",
            },
        }

        variant(
            "instance_type",
            values="c7i.12xlarge",
            default="c7i.12xlarge",
            description="AWS instance type",
        )

2. Specify the class initializer
-----------------------------
__init__

3. Add a packages section
----------------------


4. Add a compilers section
-----------------------

5. Add a software section
-----------------------


6. Validating the System
------------------------