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
   can be parameterized to match yours, otherwise proceed with adding a new system in
   :ref:`system-specification`.

.. _adding-system-hardware-specs:

A. Adding System Hardware Specs
-------------------------------

We list hardware descriptions of Systems specified in Benchpark in the System Catalogue
in :doc:`system-list`.

If you are running on a system with an accelerator, find an existing system with the
same accelerator vendor, and then secondarily, if you can, match the actual accelerator.

1. ``accelerator.vendor`` - Company name
2. ``accelerator.name`` - Product name
3. ``accelerator.ISA`` - Instruction set architecture
4. ``accelerator.uArch`` - Microarchitecture

Once you have found an existing system with a similar accelerator or if you do not have
an accelerator, match the following processor specs as closely as you can.

1. ``processor.vendor`` - Company name
2. ``processor.name`` - Product name
3. ``processor.ISA`` - Instruction set architecture
4. ``processor.uArch`` - Microarchitecture

And add the interconnect vendor and product name.

1. ``interconnect.vendor`` - Company name
2. ``interconnect.name`` - Product name

For example, if your system has an NVIDIA A100 GPU and an Intel x86 Icelake CPUs, a
similar config would share the A100 GPU, and CPU architecture may or may not match. Or,
if I do not have GPUs and instead have SapphireRapids CPUs, the closest match would be
another system with x86_64, Xeon Platinum, SapphireRapids.

If there is not an exact match, you may add a new directory in the
``systems/all_hardware_descriptions/system_name`` where ``system_name`` follows the
naming convention:

::

    [INTEGRATOR]-MICROARCHITECTURE[-ACCELERATOR][-NETWORK]

where:

::

    INTEGRATOR = COMPANY[_PRODUCTNAME][...]

    MICROARCHITECTURE = CPU Microarchitecture

    ACCELERATOR = ACCELERATOR Product Name

    NETWORK = Network Product Name

In the ``systems/all_hardware_descriptions/system_name`` directory, add a
``hardware_description.yaml`` which follows the yaml format of existing
``hardware_description.yaml`` files.

.. _system-specification:

B. Creating the System Definition (``system.py``)
-------------------------------------------------

Now that you have defined the hardware description for your system, you can now create
the ``system.py``, which involves defining the software on your system. This includes
defining compilers and pre-installed packages, which your package manager can use
instead of attempting to build the package from scratch. If using Spack, defining as
many external packages as possible here will ensure a much faster build process, and
using system-installed packages will likely always be more performant than building them
from scratch.

1. Creating the System class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, we will recreate a fully-functional example of the AWS ``system.py``
that we use for benchpark tutorials (see `aws-tutorial/system.py
<https://github.com/LLNL/benchpark/blob/develop/systems/aws-tutorial/system.py>`_). To
start, we import the base benchpark ``System`` class, which our ``AwsTutorial`` system
will inherit from. We also import the maintainer and variant directives, which provide
the utilities to track a maintainer by their GitHub username and variants to specify
configurable properties of our system. We can specify the different AWS instances that
share this same hardware and software specificaiton using the ``instance_type`` variant.
We use ``instance_type`` here instead of ``cluster`` (you will see ``cluster`` in other
systems), to differentiate a cloud ``instance`` from an HPC ``cluster``.

::

    from benchpark.directives import maintainers, variant
    from benchpark.system import System


    class AwsTutorial(System):
        maintainers("michaelmckinsey1")

        variant(
            "instance_type",
            values=("c7i.12xlarge", c7i.24xlarge),
            default="c7i.12xlarge",
            description="AWS instance type",
        )

1. Specify the class initializer and resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When defining ``__init__()`` for our system, we invoke the parent
``System::__init__()``, and set important system attributes using the
``id_to_resources`` dictionary, which contains information for each ``cluster`` or
``instance_type``. We can optionally refactor common attributes for all
``instance_type``'s into a separate dictionary, for readability:

1. ``system_site`` - The name of the site where the ``cluster``/``instance_type`` is
   located.
2. ``programming_models`` - List of applicable programming models. ``MPI`` is assumed
   for every system in benchpark, so you do not need to add it here. For this system, we
   add ``OpenMPCPUOnlySystem`` (different from GPU openmp). If we had Nvidia
   accelerators, we would add ``CudaSystem`` to this list, and ``ROCmSystem`` for AMD.
3. ``scheduler`` - The job scheduler.
4. ``hardware_key``, which defines a path to the yaml description you just created in
   the previous step.
5. ``sys_cores_per_node`` - The amount of hardware cores per node.
6. ``sys_mem_per_node_GB`` - The amount of node memory, in gigabytes.

This information is used to determine the necessary resource allocation request for any
experiment initialized with your chosen.

::

    from benchpark.directives import maintainers, variant
    from benchpark.openmpsystem import OpenMPCPUOnlySystem
    from benchpark.paths import hardware_descriptions
    from benchpark.system import System


    class AwsTutorial(System):
        maintainers("michaelmckinsey1")

        common = {
            "system_site": "aws",
            "programming_models": [OpenMPCPUOnlySystem()],
            "scheduler": "flux",
            "hardware_key": str(hardware_descriptions)
            + "/AWS_Tutorial-sapphirerapids-EFA/hardware_description.yaml",
        }

        id_to_resources = {
            "c7i.24xlarge": {
                **common,
                "sys_cores_per_node": 96,
                "sys_mem_per_node_GB": 192,
            },
            "c7i.12xlarge": {
                **common,
                "sys_cores_per_node": 48,
                "sys_mem_per_node_GB": 96,
            },
        }

        variant(
            "instance_type",
            values=("c7i.12xlarge", "c7i.24xlarge"),
            default="c7i.12xlarge",
            description="AWS instance type",
        )

        def __init__(self, spec):
            super().__init__(spec)

            attrs = self.id_to_resources.get(self.spec.variants["instance_type"][0])
            for k, v in attrs.items():
                setattr(self, k, v)

3. Add a packages section
~~~~~~~~~~~~~~~~~~~~~~~~~

Here, we define the ``compute_packages_section()`` function, where you can include any
package that you would like a package manager, such as spack, to find as an "external",
meaning it will not build that package from source and use your system package instead.
For each package that you include, you need to define its spec ``name@version`` and the
system path ``prefix`` to the package. Additionally for spack, you need to set
``buildable: False`` to use the package as an external.

At minimum, we recommend you define externals for ``cmake``, ``mpi``, ``blas``, and
``lapack``. See :ref:`adding-sys-packages`, for help on how to search for the packages
installed on your system.

.. note::

    For ``mpi``, you need to define ``"mpi": {"buildable": False},`` as a virtual
    package, and then define your MPI package as we have for ``openmpi``.

::

    from benchpark.directives import maintainers, variant
    from benchpark.openmpsystem import OpenMPCPUOnlySystem
    from benchpark.paths import hardware_descriptions
    from benchpark.system import System


    class AwsTutorial(System):

    ...


        def compute_packages_section(self):
            return {
                "packages": {
                    "tar": {
                        "externals": [{"spec": "tar@1.34", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "gmake": {"externals": [{"spec": "gmake@4.3", "prefix": "/usr"}]},
                    "lapack": {
                        "externals": [{"spec": "lapack@0.29.2", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "mpi": {"buildable": False},
                    "openmpi": {
                        "externals": [
                            {
                                "spec": "openmpi@4.0%gcc@11.4.0",
                                "prefix": "/usr",
                            }
                        ]
                    },
                    "cmake": {
                        "externals": [{"spec": "cmake@4.0.2", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "git": {
                        "externals": [{"spec": "git@2.34.1~tcltk", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "openssl": {
                        "externals": [{"spec": "openssl@3.0.2", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "automake": {
                        "externals": [{"spec": "automake@1.16.5", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "openssh": {
                        "externals": [{"spec": "openssh@8.9p1", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "m4": {
                        "externals": [{"spec": "m4@1.4.18", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "sed": {
                        "externals": [{"spec": "sed@4.8", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "autoconf": {
                        "externals": [{"spec": "autoconf@2.71", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "diffutils": {
                        "externals": [{"spec": "diffutils@3.8", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "coreutils": {
                        "externals": [{"spec": "coreutils@8.32", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "findutils": {
                        "externals": [{"spec": "findutils@4.8.0", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "binutils": {
                        "externals": [
                            {"spec": "binutils@2.38+gold~headers", "prefix": "/usr"}
                        ],
                        "buildable": False,
                    },
                    "perl": {
                        "externals": [
                            {
                                "spec": "perl@5.34.0~cpanm+opcode+open+shared+threads",
                                "prefix": "/usr",
                            }
                        ],
                        "buildable": False,
                    },
                    "caliper": {
                        "externals": [
                            {
                                "spec": "caliper@master+adiak+mpi%gcc@11.4.0",
                                "prefix": "/usr",
                            }
                        ],
                        "buildable": False,
                    },
                    "adiak": {
                        "externals": [{"spec": "adiak@0.4.1", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "groff": {
                        "externals": [{"spec": "groff@1.22.4", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "curl": {
                        "externals": [
                            {"spec": "curl@7.81.0+gssapi+ldap+nghttp2", "prefix": "/usr"}
                        ],
                        "buildable": False,
                    },
                    "ccache": {
                        "externals": [{"spec": "ccache@4.5.1", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "flex": {
                        "externals": [{"spec": "flex@2.6.4+lex", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "pkg-config": {
                        "externals": [{"spec": "pkg-config@0.29.2", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "zlib": {
                        "externals": [{"spec": "zlib@1.2.11", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "ninja": {
                        "externals": [{"spec": "ninja@1.10.1", "prefix": "/usr"}],
                        "buildable": False,
                    },
                    "libtool": {
                        "externals": [{"spec": "libtool@2.4.6", "prefix": "/usr"}],
                        "buildable": False,
                    },
                }
            }

4. Add a compilers section
~~~~~~~~~~~~~~~~~~~~~~~~~~

In the ``compute_compilers_section``, we define the compilers available on the system.
For our AWS system, this is ``gcc@11.4.0``. We return a dictionary, with the helper
``compiler_section_for()`` function, that formulates the compiler ``name`` and
``entries`` for Spack, where the ``entries`` are a list of ``compiler_def()``. For the
``compiler_def()``, we must at minimum specify the ``spec``, ``prefix``, and ``exes``:

1. ``spec`` - Similar to package specs, ``name@version``. GCC in particular also needs
   the ``languages=c,c++,fortran`` variant.
2. ``prefix`` - Prefix to the compiler binary directory, e.g. ``/usr/`` for
   ``/usr/bin/gcc``
3. ``exes`` - Dictionary to map ``c``, ``cxx``, ``fortran`` to the appropriate file
   found in the prefix.

::

    from benchpark.directives import maintainers, variant
    from benchpark.openmpsystem import OpenMPCPUOnlySystem
    from benchpark.paths import hardware_descriptions
    from benchpark.system import System, compiler_def, compiler_section_for


    class AwsTutorial(System):

    ...

        def compute_compilers_section(self):
            return compiler_section_for(
                "gcc",
                [
                    compiler_def(
                        "gcc@11.4.0 languages=c,c++,fortran",
                        "/usr/",
                        {"c": "gcc", "cxx": "g++", "fortran": "gfortran-11"},
                    )
                ],
            )

5. Add a software section
~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, we define the ``compute_software_section()``, where at minimum we must define
the ``default-compiler`` for Ramble. This is trivial for the single compiler that we
have ``gcc@11.4.0``.

::

    from benchpark.directives import maintainers, variant
    from benchpark.openmpsystem import OpenMPCPUOnlySystem
    from benchpark.paths import hardware_descriptions
    from benchpark.system import System, compiler_def, compiler_section_for


    class AwsTutorial(System):

    ...

        def compute_software_section(self):
            return {
                "software": {
                    "packages": {
                        "default-compiler": {"pkg_spec": "gcc@11.4.0"},
                    }
                }
            }

6. Validating the System
~~~~~~~~~~~~~~~~~~~~~~~~

To manually validate that your new system works, you should start by initializing your
system:

::

    benchpark system init --dest=aws-tutorial aws-tutorial

If this completes without errors, you can continue by creating a benchmark
:doc:`add-a-benchmark`.

System Appendix
---------------

.. _adding-sys-packages:

1. Adding/Updating System Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

External package definitions can be added/updated from the output of ``benchpark system
external``. If you don't have any packages yet, define ``compute_packages_section`` as
an empty dictionary:

::

    def compute_packages_section(self):
        return {
            "packages": {}
        }

And then whether or not you have packages, run ``benchpark system external <system>
cluster=<cluster>``:

::

    [ruby]$ benchpark system external llnl-cluster cluster=ruby

    $ benchpark system external llnl-cluster
    ==> The following specs have been detected on this system and added to /g/g20/mckinsey/.benchmark/spack/etc/spack/packages.yaml
    cmake@3.23.1  cmake@3.26.5  gmake@4.2.1  hwloc@2.11.2  python@2.7.18  python@2.7.18  python@3.6.8  python@3.9.12  python@3.10.8  python@3.12.8  tar@1.30
                    The Packages are different. Here are the differences:
    {'dictionary_item_added': ["root['gmake']['buildable']"],
    'dictionary_item_removed': ["root['elfutils']", "root['papi']", "root['unwind']", "root['blas']", "root['lapack']", "root['fftw']", "root['mpi']"],
    'iterable_item_added': {"root['cmake']['externals'][1]": {'prefix': '/usr/tce',
                                                              'spec': 'cmake@3.23.1'},
                            "root['python']['externals'][1]": {'prefix': '/usr',
                                                                'spec': 'python@2.7.18+bz2+crypt+ctypes+dbm~lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl~tkinter+uuid+zlib'},
                            "root['python']['externals'][2]": {'prefix': '/usr',
                                                                'spec': 'python@3.6.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                            "root['python']['externals'][3]": {'prefix': '/usr/tce',
                                                                'spec': 'python@2.7.18+bz2+crypt+ctypes+dbm~lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                            "root['python']['externals'][4]": {'prefix': '/usr/tce',
                                                                'spec': 'python@3.9.12+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                            "root['python']['externals'][5]": {'prefix': '/usr/workspace/wsa/mckinsey/venv/benchpark-3.12.8',
                                                                'spec': 'python@3.12.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat+pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'}},
    'values_changed': {"root['cmake']['externals'][0]['prefix']": {'new_value': '/usr',
                                                                    'old_value': '/usr/tce/packages/cmake/cmake-3.26.3'},
                        "root['cmake']['externals'][0]['spec']": {'new_value': 'cmake@3.26.5',
                                                                  'old_value': 'cmake@3.26.3'},
                        "root['hwloc']['externals'][0]['spec']": {'new_value': 'hwloc@2.11.2',
                                                                  'old_value': 'hwloc@2.9.1'},
                        "root['python']['externals'][0]['prefix']": {'new_value': '/usr/WS1/mckinsey/venv/python-3.10.8',
                                                                    'old_value': '/usr/tce/packages/python/python-3.9.12/'},
                        "root['python']['externals'][0]['spec']": {'new_value': 'python@3.10.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat+pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib',
                                                                  'old_value': 'python@3.9.12'}}}
                    Here are all of the new packages:
    {'cmake': {'buildable': False,
              'externals': [{'prefix': '/usr', 'spec': 'cmake@3.26.5'},
                            {'prefix': '/usr/tce', 'spec': 'cmake@3.23.1'}]},
    'gmake': {'buildable': False,
              'externals': [{'prefix': '/usr', 'spec': 'gmake@4.2.1'}]},
    'hwloc': {'buildable': False,
              'externals': [{'prefix': '/usr', 'spec': 'hwloc@2.11.2'}]},
    'python': {'buildable': False,
                'externals': [{'prefix': '/usr/WS1/mckinsey/venv/python-3.10.8',
                              'spec': 'python@3.10.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat+pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                              {'prefix': '/usr',
                              'spec': 'python@2.7.18+bz2+crypt+ctypes+dbm~lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl~tkinter+uuid+zlib'},
                              {'prefix': '/usr',
                              'spec': 'python@3.6.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                              {'prefix': '/usr/tce',
                              'spec': 'python@2.7.18+bz2+crypt+ctypes+dbm~lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                              {'prefix': '/usr/tce',
                              'spec': 'python@3.9.12+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat~pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'},
                              {'prefix': '/usr/workspace/wsa/mckinsey/venv/benchpark-3.12.8',
                              'spec': 'python@3.12.8+bz2+crypt+ctypes+dbm+lzma+nis+pyexpat+pythoncmd+readline+sqlite3+ssl+tix+tkinter+uuid+zlib'}]},
    'tar': {'buildable': False,
            'externals': [{'prefix': '/usr', 'spec': 'tar@1.30'}]}}

where the command should be ran on a cluster that is defined for the given system, e.g.
ruby for llnl-cluster. Use this output to update your package definitions in your
``system.py``'s ``compute_package_section()``.

For packages that are not found by ``benchpark system external``, you can manually find
them using a command like the ``module`` command:

::

    [dane6:~]$ module display gcc/12.1.1
    ...
    prepend_path("PATH","/usr/tce/packages/gcc/gcc-12.1.1/bin")

Therefore, I can add my ``prefix`` as ``/usr/tce/packages/gcc/gcc-12.1.1/`` and my spec
as ``gcc@12.1.1``.
