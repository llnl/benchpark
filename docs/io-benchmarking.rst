..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

Using File Systems
==================

For benchmarks that need to run on a different file system, benchpark defines per-system
variants, which experiments can use to leverage specific file systems.

1. For file systems that require a scheduler request
----------------------------------------------------

Check if the ``system`` you are attempting to initialize has a variant supporting your
desired file system. If it does not, first add a variant that describes the different
options. For example, the ``llnl-elcapitan`` system has ``rabbit`` storage available via
a flux scheduler request. We specify the options with a ``rabbit_config`` variant:

::

    variant(
        "rabbit_config",
        default="none",
        values=("none", "xfs_small", "xfs_large", "lustre_small", "lustre_large", "gfs2_small", "gfs2_large"),
        multi=False,
        description="Rabbit configurations",
    )

These are the different options that we can specify to the ``flux`` scheduler, for
different configurations of rabbit storage. Then, in the ``system_specific_variables()``
function, we can add the selected variant to all batch jobs generated using this system
definition, using the ``extra_batch_opts`` keyword.

::

    def system_specific_variables(self):
        opts = super().system_specific_variables()
        extra_batch_opts = ""

        rb_config = self.spec.variants['rabbit_config'][0]
        if rb_config != "none":
            extra_batch_opts += f"\n-S dw={rb_config}"
        opts.update(
            {
                "extra_batch_opts": extra_batch_opts,
            }
        )

2. How to use a different path in your application
--------------------------------------------------

Check if the ``system`` you are attempting to initialize has a ``mount_point`` variant,
such as:

::

    variant(
        "mount_point",
        default="none",
        values=("none", "/p/lustre5"),
        multi=False,
        description="Which mount point to use for IO benchmarks"
    )

If it does, check to see if the ``mount_point`` variant is referenced in the
``experiment`` that you wish to run. Because experiments are intialized with a specific
system, we can reference the ``mount_point`` system variant in our experiment. Here, we
see an example in the ``ior`` experiment, which uses the ``mount_point`` to determine
where test files should be created (the ``-o`` command line argument):

::

    mount_point = self.system_spec.system.spec.variants["mount_point"][0]
    self.add_experiment_variable("o", mount_point + "/$USER/test.bat")
