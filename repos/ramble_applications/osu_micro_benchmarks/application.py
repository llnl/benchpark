# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.app.builtin.osu_micro_benchmarks import (
    OsuMicroBenchmarks as OsuMicroBenchmarksBase,
)
from ramble.appkit import *


class OsuMicroBenchmarks(OsuMicroBenchmarksBase):

    tags = ['synthetic',
            'large-scale','multi-node','single-node',
            'atomics','managed-memory',
            'mpi','openshmem','upc','upc++','nccl','rccl',
            'network-bandwidth-bound','network-bisection-bandwidth-bound',
            'network-collectives','network-latency-bound',
            'network-multi-threaded','network-nonblocking-collectives',
            'network-onesided','network-point-to-point',
            'c','java','python','openacc']

    workload_group(
        "two_rank_workloads",
        workloads=[
            "osu_bibw",
            "osu_bw",
            "osu_latency",
            "osu_get_acc_latency",
            "osu_get_bw",
            "osu_get_latency",
            "osu_put_bibw",
            "osu_put_bw",
            "osu_put_latency",
            ]
        )

    register_validator(
        name="two_rank_workloads",
        predicate="{n_ranks} != 2",
        workload_group="two_rank_workloads",
        message="This test requires exactly two processes."
        )
