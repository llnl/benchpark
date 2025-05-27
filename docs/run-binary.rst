.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

=================================
Running a Binary Using Benchpark
=================================

If you have a pre-built binary of your application, you can use it in your Benchpark experiment using the `None` package manager. 
When initializing your experiment, provide the path to the binary, and specify `None` as the package manager.
The steps for initializing the system and setting up the experiment remain the same as before.

Example running the `osu-micro-benchmarks` workload `osu_latency` on the `ruby` system::

    benchpark experiment init --dest=osumb osu-micro-benchmarks \
        package_manager="None" \
        workload="osu_latency" \
        append_path="osu-micro-benchmarks/mpi/pt2pt"
    benchpark system init --dest=ruby llnl-cluster cluster=ruby
    benchpark setup ./osumb/ ./ruby/ osumb-ruby/
