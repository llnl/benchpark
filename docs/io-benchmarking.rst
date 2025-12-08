..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

####################
 Using File Systems
####################

For benchmarks that need to run on a different file system, benchpark defines per-system
variants, which experiments can use to leverage specific file systems.

****************************************************************
 1. How to enable writing to a file system on a specific system
****************************************************************

Check if the ``system`` you are attempting to initialize has a ``mount_point`` variant,
with ``benchpark info system SYSTEM``:

::

    $ benchpark info system llnl-elcapitan

    name: mount_point
    default: none
    description: Which mount point to use for IO benchmarks
    values: ('none', '/l/ssd', '/p/lustre1', '/p/lustre2', '/p/lustre3', '/p/lustre4', '/p/lustre5', 'rabbits_xfs_small', 'rabbits_xfs_large', 'rabbits_lustre_small', 'rabbits_lustre_large', 'rabbits_gfs2_small', 'rabbits_gfs2_large')
    validator: <function Variant.__init__.<locals>.<lambda> at 0x15542a719e40>
    multi: False
    sticky: False

And also check in the output which of the mount points are valid for your chosen
cluster, such as for ``cluster=tuolumne``:

::

    tuolumne:
        ...
        mount_points: ['/l/ssd', '/p/lustre5', 'rabbits_xfs_small', 'rabbits_xfs_large', 'rabbits_lustre_small', 'rabbits_lustre_large', 'rabbits_gfs2_small', 'rabbits_gfs2_large']

If the mount points are defined for your chosen system and cluster, you can reference
``self.system_spec.system.full_io_path`` in your experiment to get the full path to that
mount point. Here, we see an example in the ``ior`` experiment, which uses the mount
point to determine where test files should be created (the ``-o`` command line
argument):

::

    full_path = self.system_spec.system.full_io_path
    self.add_experiment_variable("o", full_path)

**************************************************************************
 2. How to add filesystem details to scheduler request `extra_batch_opts`
**************************************************************************

If the ``system`` you are attempting to initialize has a variant supporting your desired
file system, you may also need to specify additional configuration details to the
scheduler. For example, the ``llnl-elcapitan`` system has ``rabbits`` storage available
via a flux scheduler request; we use the ``io_config`` variant to add these options to
the ``extra_batch_opts`` in the flux request:

::

    variant(
        "mount_point",
        default="none",
        values=(
            "none",
            "/l/ssd",
            "/p/lustre1",
            "/p/lustre2",
            "/p/lustre3",
            "/p/lustre4",
            "/p/lustre5",
            "rabbits_xfs_small",
            "rabbits_xfs_large",
            "rabbits_lustre_small",
            "rabbits_lustre_large",
            "rabbits_gfs2_small",
            "rabbits_gfs2_large",
        ),
        multi=False,
        description="Which mount point to use for IO benchmarks",
    )

The ``rabbit_*`` options are the different options that we can specify to the ``flux``
scheduler, for different configurations of rabbits storage. Then, in the
``system_specific_variables()`` function, we can add the selected variant to all batch
jobs generated using this system definition, using the ``extra_batch_opts`` keyword:

::

    def system_specific_variables(self):
        opts = super().system_specific_variables()
        extra_batch_opts = ""

        mt_point = self.spec.variants["mount_point"][0]
        if mt_point != "none" and "rabbits" in mt_point:
            extra_batch_opts += f"\n-S dw={mt_point.lstrip('rabbits_')}"
