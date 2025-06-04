# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import re
import json
from collections import defaultdict
import xmltodict


def parse_hwloc_tree_full_metadata(obj, path="topology", results=None, counters=None):
    if results is None:
        results = []
    if counters is None:
        counters = defaultdict(int)

    if isinstance(obj, dict):
        raw_type = obj.get("@type", "Unknown")
        counter = counters[raw_type]
        counters[raw_type] += 1

        type_display = f"{raw_type}[{counter}]"

        node_info = {
            "type": raw_type,
            "instance": counter,
        }

        for key, value in obj.items():
            if isinstance(value, (str, int, float)):
                node_info[key] = value

        if "info" in obj and isinstance(obj["info"], list):
            for item in obj["info"]:
                k = item.get("@name")
                v = item.get("@value")
                if k:
                    node_info[k] = v

        full_path = f"{path}/{type_display}"
        results.append((full_path, node_info))

        if "object" in obj:
            children = obj["object"]
            if isinstance(children, list):
                for child in children:
                    parse_hwloc_tree_full_metadata(child, full_path, results, counters)

            elif isinstance(children, dict):
                parse_hwloc_tree_full_metadata(children, full_path, results, counters)

    elif isinstance(obj, list):
        for item in obj:
            parse_hwloc_tree_full_metadata(item, path, results, counters)

    return results


def clean_keys(d):
    if isinstance(d, dict):
        return {k.lstrip("@"): clean_keys(v) for k, v in d.items()}

    elif isinstance(d, list):
        return [clean_keys(i) for i in d]

    else:
        return d


def parse_lstopo_summary(hwloc_xml_file_path, hwloc_output_json_file_path):
    try:
        with open(hwloc_xml_file_path, "r") as xml_file:
            lines = xml_file.readlines()

        print("lines length", len(lines))
        # 1) Filter lines that appear to be XML tags or declarations, because sometimes lstopo prints warnings/errors
        xml_like_lines = [line for line in lines if re.match(r"\s*<[^>]+>", line)]

        if not xml_like_lines:
            raise ValueError("No valid XML lines found in the file.")

        xml_content = "".join(xml_like_lines)
        data_dict = xmltodict.parse(xml_content)

        # 2) Traverse, flatten, and clean the generated json
        parsed_pairs = parse_hwloc_tree_full_metadata(data_dict["topology"]["object"])
        flat_dict = {path: metadata for path, metadata in parsed_pairs}
        cleaned_flat_dict = {
            path: clean_keys(metadata) for path, metadata in flat_dict.items()
        }

        # 3) Make resource name and its count as the key, and add its path as attribute
        shortened_dict = {}
        for full_path, metadata in cleaned_flat_dict.items():
            *prefix, final_key = full_path.split("/")
            metadata_with_path = dict(metadata)
            metadata_with_path["path"] = "/".join(prefix)
            shortened_dict[final_key] = metadata_with_path

        # 4) Persist the json
        with open(hwloc_output_json_file_path, "w") as f:
            json.dump(shortened_dict, f, indent=2)

    except Exception as e:
        raise ValueError(f"Failed to convert Hwloc XML to JSON: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="hwloc output to JSON")
    parser.add_argument(
        "hwloc_xml_log_file", type=str, help="hwloc output in xml format"
    )
    parser.add_argument(
        "hwloc_json_log_file", type=str, help="hwloc output in json format"
    )
    parser.add_argument("mode", type=str, help="hwloc mode(text)")

    args = parser.parse_args()

    parse_lstopo_summary(args.hwloc_xml_log_file, args.hwloc_json_log_file)
