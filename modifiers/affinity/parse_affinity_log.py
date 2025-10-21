# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import re
from pathlib import Path


def parse_affinity(affinity_log_file, mode):
    with open(affinity_log_file, "r") as f:
        lines = f.readlines()

    affinity_map = {"gpus": [], "cores": []}

    current_rank = None
    current_node = None

    for line in lines:
        # Match rank and node
        rank_match = re.match(r"rank\s+(\d+)\s+@\s+(\S+)", line)
        if rank_match:
            current_rank = int(rank_match.group(1))
            current_node = rank_match.group(2)
            continue

        # Match CPU affinity (cores)
        core_match = re.match(r"\s*cores\s*:\s*(\d+)", line)
        if core_match and current_rank is not None:
            affinity_map["cores"].append(
                {
                    "rank": current_rank,
                    "node": current_node,
                    "cores": int(core_match.group(1)),
                }
            )
            continue

        if mode == "cuda" or mode == "rocm":
            # Match GPU affinity
            gpu_match = re.match(r"\s*gpu\s*\d+\s*:\s*(GPU-\S+)", line)
            if gpu_match and current_rank is not None:
                affinity_map["gpus"].append(
                    {
                        "rank": current_rank,
                        "node": current_node,
                        "gpu_id": gpu_match.group(1),
                    }
                )
                continue

    # Save to JSON file
    output_file = Path(affinity_log_file).with_suffix(".json")
    with open(output_file, "w") as json_file:
        json.dump(affinity_map, json_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="affinity output to JSON")
    parser.add_argument("affinity_log_file", type=str, help="affinity log file (text)")
    parser.add_argument(
        "mode", choices=["mpi", "cuda", "rocm"], help="Mode: 'mpi', 'cuda' or 'rocm'"
    )

    args = parser.parse_args()
    parse_affinity(args.affinity_log_file, args.mode)
