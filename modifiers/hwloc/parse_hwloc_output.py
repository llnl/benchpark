import re
import json
import argparse
from pathlib import Path


def parse_lstopo_summary(file_path):
    summary = {
        "depths": [],
        "special_depths": [],
        "numa_latency_matrix": []
    }

    with open(file_path, 'r') as f:
        lines = f.readlines()

    in_latency = False
    for line in lines:
        line = line.strip()

        # Parse standard depth lines
        match_depth = re.match(r'^depth (\d+):\s+(\d+)\s+(\S.+?) \(type #(\d+)\)', line)
        if match_depth:
            depth, count, name, type_num = match_depth.groups()
            summary["depths"].append({
                "depth": int(depth),
                "count": int(count),
                "name": name.strip(),
                "type": int(type_num)
            })
            continue

        # Parse special depth lines
        match_special = re.match(r'^Special depth (-\d+):\s+(\d+)\s+(\S.+?) \(type #(\d+)\)', line)
        if match_special:
            depth, count, name, type_num = match_special.groups()
            summary["special_depths"].append({
                "depth": int(depth),
                "count": int(count),
                "name": name.strip(),
                "type": int(type_num)
            })
            continue

        # Start of NUMA latency matrix
        if "Relative latency matrix" in line:
            in_latency = True
            continue

        if in_latency:
            if line.startswith("CPU kind") or not line:
                in_latency = False
                continue
            else:
                values = line.split()
                summary["numa_latency_matrix"].append(values)

    return summary


def save_summary_to_json(summary_data, hwloc_log_file):
    output_file = Path(hwloc_log_file).with_suffix(".json")
    with open(output_file, 'w') as f:
        json.dump(summary_data, f, indent=2)


# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="hwloc output to JSON")
    parser.add_argument("hwloc_log_file", type=str, help="hwloc output file (text)")
    parser.add_argument("mode", type=str, help="hwloc mode(text)")

    args = parser.parse_args()
    summary = parse_lstopo_summary(args.hwloc_log_file)

    save_summary_to_json(summary, args.hwloc_log_file)
