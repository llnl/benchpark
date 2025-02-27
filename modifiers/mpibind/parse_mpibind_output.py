# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import json
import re
import argparse


def parse_mpibind(input_file):

    with open(input_file, "r") as f:
        lines = f.readlines()

    task_map = {}

    for line in lines:

        # Match lines beginning with "mpibind:"
        mpibind_match = re.match(r"^mpibind:.*(?:\r?\n|$)", line)
        if mpibind_match:

            pattern = r"task\s+(\d+)\s+nths\s+([\d,]*)\s+gpus\s+([\d,]*)\s+cpus\s+([\d,]*-[\d,]*)"
            match = re.search(pattern, line)
            if match:
                task = match.group(1)  # Task number
                nths = match.group(2)  # Nths value
                gpus = match.group(3)  # GPUs value
                cpus = match.group(4)  # CPUs value

                task_map["task " + task] = {
                    "cpus": cpus,
                    "gpus": gpus,
                    "nths": nths,
                }

    output_file = "mpibind_log_file.json"
    with open(output_file, "w") as json_file:
        json.dump(task_map, json_file, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="affinity output to JSON")
    parser.add_argument("output_file", type=str, help="mpibind log file (text)")

    args = parser.parse_args()
    parse_mpibind(args.output_file)
