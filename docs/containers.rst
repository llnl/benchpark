..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

############################
 Tutorial: Local Containers
############################

This tutorial will walk you through getting Benchpark running in your own local
container. There are some known issues and bugs, but one advantage to working in a local
container is you can test basic benchmarks and process and analyze output without having
to work through running on a real cluster.

*************************************************
 Step 1: Getting Started with Container Runtimes
*************************************************

If you haven't used containers on your local system before, allow us to recommend the
`Podman Desktop <https://podman-desktop.io/>` container runtime suite. It can be
installed using the instructions from their official site or with ``brew``. It is free
and quite robust. The CLI is more or less the same, so if you are following along with
Docker, the commands here should work equally well, but let us know if that is not the
case.

**Some Changes to the Default VM**

For the purposes of this tutorial, I recommend setting at least 8 cores and about 16 GiB
of memory as follows:

..
    code-block::bash

    podman machine stop
    podman machine set --cpus=8 --memory 15258
    podman machine start

**Some Common Issues**

If you are behind a firewall, you may need to tell your VM about the firewall
self-signed certificate to avoid errors involving pulling containers. Here is an example
for macOS:

..
    code-block::bash

        security find-certificate -a -p /Library/Keychains/System.keychain | \
    podman machine ssh sudo tee /etc/pki/ca-trust/source/anchors/macos-system-certs.pem > /dev/null

and then you will need to restart the machine as above.

**********************************************
 Step 2: Playing with the Benchpark Container
**********************************************

Now, let's pull and run a Benchpark Container:

..
    code-block::bash

    podman pull ghcr.io/llnl/benchpark/benchpark-flux-el10
    podman run -it benchpark-flux-el10

And now, if everything worked properly, you should be dropped into a shell that is
already running Flux and Benchpark. The Flux broker has been tricked into thinking the
container has 4 nodes with 8 cores each. ``mpibind`` has also been installed as a Flux
plugin, and is managing "affinity" on the various "nodes." A simple MPICH installation
is also installed and available.

**Some simple Benchpark commands**

Let's run some simple Benchpark commands to poke around:

::

    $ benchpark list systems

.. program-output:: ../bin/benchpark list systems
    :ellipsis: 10

This will show you all the systems available. This particular one is called
``fluxtainer``. Let's get some more info on it:

::

    $ benchpark info system fluxtainer

.. program-output:: ../bin/benchpark info system fluxtainer


In the output, we can see that there is a ``variant`` called ``instance_type``. Let's
keep that in mind as we initialize the system. In my case, the architecture is ``arm``,
but yours might be ``x86``.

..
    code-block::bash

    benchpark system init --dest=my-fluxtainer fluxtainer instance_type=arm

Okay now let's look at some benchmarks:

::

    $ benchpark list experiments

.. program-output:: ../bin/benchpark list experiments


Let's look at the ``osu-micro-benchmarks``:

::

    $ benchpark info experiment osu-micro-benchmarks

.. program-output:: ../bin/benchpark info experiment osu-micro-benchmarks


Okay that was a lot to take in. Most of it is ``variants`` yet again. We'll discuss a
couple in detail: ``affinity`` will run the `affinity
<https://github.com/bcumming/affinity>` test to show where different communicating
processes ended up *within* a node, be they MPI ranks or OpenMP threads, on CPU cores or
GPUs. This can be very helpful for debugging common parallel performance issues.

The other variant to look at is ``workload``. This variant will determine which actual
micro- benchmarks get run. Okay, let's get started with a simple example, but first some
caveats:

**Caveats and known issues**

1. The OSU benchmarks are a work in progress, and we are still working out the details
on scaling ranks at this stage, so we will stick with 2 ranks on 2 fake nodes. 

2.  Collectives *can* hang in this configuration as this multi-node trick we're playing on
the Flux broker is really more for testing broker throughput, scheduling algorithms,
etc., not actual applications. We will demonstrate a more robust single-node
configuration a bit later.

Okay now that we have that out of the way, let's initialize, setup, and run an
experiment:

..
    code-block::bash

    benchpark experiment init my-fluxtainer osu-micro-benchmarks workload=osu_allreduce,osu_mbw_mr affinity=on

Now we get a message back telling us what to run next:

..
    code-block::text

    Run `benchpark setup my-fluxtainer/osu-micro-benchmarks <experiments_root>` to generate Ramble workspace

Let's call the ``experiments_root`` ``wkp`` for now...

..
    code-block::bash

    benchpark setup my-fluxtainer/osu-micro-benchmarks wkp

If you get the error

..
    code-block::text

    fatal: hardlink different from source at ...

Run:

..
    code-block::bash

    rm -rf ~/.benchpark
    benchpark bootstrap

and reattempt the above ``benchpark setup ...`` command. And yet again, Benchpark tells
us what to run next:

..
    code-block::text

    Clearing existing workspace /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks
    Setting up configs for Ramble workspace /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/configs
    Cloning packages to /home/fluxuser/benchpark/wkp/spack-packages
    Cloning Spack to /home/fluxuser/benchpark/wkp/spack
    Cloning Ramble to /home/fluxuser/benchpark/wkp/ramble
    To complete the benchpark setup, do the following:

            . /home/fluxuser/benchpark/wkp/setup.sh

    Further steps are needed to build the experiments (ramble --workspace-dir /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace workspace setup) and run them (ramble --workspace-dir /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace on)

So let's do that:

..
    code-block::bash

    . /home/fluxuser/benchpark/wkp/setup.sh
    ramble --workspace-dir /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace workspace setup
    ramble --workspace-dir /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace on

And Ramble tells us it built the software:

..
    code-block::text
    ==> Streaming details to log:
    ==>   /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/setup.2026-05-06_23.38.34.out
    ==>   Setting up 2 out of 2 experiments:
    ==> Experiment #1 (1/2):
    ==>     name: osu_micro_benchmarks.osu_allreduce.osu_micro_benchmarks_osu_allreduce_test_mpi_2_2
    ==>     root experiment_index: 1
    ==>     log file: /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/setup.2026-05-06_23.38.34/osu_micro_benchmarks.osu_allreduce.osu_micro_benchmarks_osu_allreduce_test_mpi_2_2.out
    ==>   Returning to log file: /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/setup.2026-05-06_23.38.34.out
    ==> Experiment #2 (2/2):
    ==>     name: osu_micro_benchmarks.osu_mbw_mr.osu_micro_benchmarks_osu_mbw_mr_test_mpi_2_2
    ==>     root experiment_index: 2
    ==>     log file: /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/setup.2026-05-06_23.38.34/osu_micro_benchmarks.osu_mbw_mr.osu_micro_benchmarks_osu_mbw_mr_test_mpi_2_2.out
    ==>   Returning to log file: /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/setup.2026-05-06_23.38.34.out

And Ramble and Flux tell us they ran the jobs:

..
    code-block::text

    ==> Streaming details to log:
    ==>   /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/execute.2026-05-06_23.43.29.out
    ==>   Executing 2 out of 2 experiments:
    ==>   Log files for experiments are stored in: /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/execute.2026-05-06_23.43.29
    ==> Running executors...
    ƒJMvePMyZ
    ƒJMxjxM5q

So what just happened?

First, Benchpark copied Spack, its packages repository (with all the build recipes), and
Ramble into a dedicated workspace for this experiment. This creates total isolation
between benchmarks and reproducibility.

Second, Ramble built our benchmarks in accordance with the instructions given in the
initialization, and also set up the batch scripts for the job scheduler (in this case
Flux).

Finally, Ramble executed the benchmarks using the Flux scheduler.

Now let's analyze the results:

..
    code-block::bash

    ramble --workspace-dir /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace workspace analyze -f json

And Ramble tells us it performed the analysis:

..
    code-block::text

    ==> Streaming details to log:
    ==>   /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/analyze.2026-05-06_23.46.25.out
    ==>   Analyzing 2 out of 2 experiments:
    ==> Experiment #1 (1/2):
    ==>     name: osu_micro_benchmarks.osu_allreduce.osu_micro_benchmarks_osu_allreduce_test_mpi_2_2
    ==>     root experiment_index: 1
    ==>     log file: /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/analyze.2026-05-06_23.46.25/osu_micro_benchmarks.osu_allreduce.osu_micro_benchmarks_osu_allreduce_test_mpi_2_2.out
    ==> Invalidating experiment results cache: timestamp difference
    ==>   Returning to log file: /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/analyze.2026-05-06_23.46.25.out
    ==> Experiment #2 (2/2):
    ==>     name: osu_micro_benchmarks.osu_mbw_mr.osu_micro_benchmarks_osu_mbw_mr_test_mpi_2_2
    ==>     root experiment_index: 2
    ==>     log file: /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/analyze.2026-05-06_23.46.25/osu_micro_benchmarks.osu_mbw_mr.osu_micro_benchmarks_osu_mbw_mr_test_mpi_2_2.out
    ==> Invalidating experiment results cache: timestamp difference
    ==>   Returning to log file: /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/logs/analyze.2026-05-06_23.46.25.out
    ==> Results are written to:
    ==>   /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/results/results.2026-05-06_23.46.26.json
    ==> Symlinks updated:
    ==>   /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/results/results.latest.json

So let's look at one:

..
    code-block::bash

    cat /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/results/results.latest.json | jq

If you scroll around, you'll see that Ramble captured quite a bit of information about
our benchmarks, most importantly, the performance data.

Hey remember we set ``affinity=on``? Where did that end up? Let's poke around this
workspace and see:

..
    code-block::bash

    cat /home/fluxuser/benchpark/wkp/my-fluxtainer/osu-micro-benchmarks/workspace/experiments/osu_micro_benchmarks/osu_allreduce/osu_micro_benchmarks_osu_allreduce_test_mpi_2_2/affinity.mpi.out

Shows:

..
    code-block::text

    affinity test for 2 MPI ranks
    rank   0 @ d26f4eea6a52: thread 0 -> core   0
    rank   1 @ d26f4eea6a52: thread 0 -> core   0

Okay not super interesting because the broker was tricked into thinking it had 4 nodes,
but this will certainly come in handy for more complex cases...

*******************************************************
 Epilogue: Gory Details, FAQ, and HPC Common Practices
*******************************************************

    What is Flux and why are you using it here?

The `Flux Framework <https://flux-framework.readthedocs.io/en/latest/>` is the *only*
workload manager on the `El Capitan
<https://hpc.llnl.gov/hardware/compute-platforms/el-capitan>` supercomputer. It is a
hierarchical, highly-portable, security-aware workload manager and job scheduler that
plays nice with cloud, containers, orchestrators, and more. We're using it here because:

1. It works well in a container.
2. It can run under other workload managers such as Slurm, Spectrum LSF, etc., so you
   can run it easily on your own cluster.

       This seems complicated.

You're right, it is, but portable reproducible benchmarking across many different system
types has a great deal of inherent complexity. Many have built test harnesses that
either compromise on one of those features or slowly grows more complex with time in an
unsustainable manner. Benchpark and Ramble take the complexity bull by the horns and use
much of `Spack <https://spack.io>`'s design philosophy to pay the cost up-front. The
learning curve is admittedly somewhat steep, but the payoff is (hopefully) portability
and reproducibility with a relatively stable set of interfaces.

    How did you build this container? Which of these lessons can I apply to my own
    cluster?

The containerfile for this particular container is `here
<https://github.com/llnl/benchpark/blob/b872919ccdc5b0171f999eed545162ae55cc2b11/containerfiles/flux/el10/Dockerfile>`.
We based it on the Flux containers and picked EL10 because that's a common OS for HPC
with a relatively stable ABI, which is important when building so much from source. The
2 key tricks it demonstrates for HPC/AI practitioners are:

1. Manage affinity portably with a tool like `mpibind
   <https://github.com/llnl/mpibind>`.
2. Describe and build on system externals deterministically with Spack.

More on how to do that second part for your own cluster is featured in :doc:`Adding a
System <.add-a-system-config>`.
