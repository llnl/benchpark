# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import re
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


def extract_commons(shortened_dict):
    result = {}

    resource_fields = {
        "L1Cache": [
            "cache_size",
            "cache_linesize",
            "cache_associativity",
            "cache_type",
        ],
        "L2Cache": [
            "cache_size",
            "cache_linesize",
            "cache_associativity",
            "cache_type",
        ],
        "L3Cache": [
            "cache_size",
            "cache_linesize",
            "cache_associativity",
            "cache_type",
        ],
        "NUMANode": ["local_memory"],
        "Package": [],
        "Core": [],
        "Machine": ["OSName", "OSRelease", "OSVersion", "HostName", "Architecture"],
        "OSDev": [
            "GPUVendor",
            "GPUModel",
            "RSMIVRAMSize",
            "RSMIVisibleVRAMSize",
            "subtype",
            "Backend",
        ],
    }

    # Fields that should be renamed to per_resource
    per_resource_fields = {
        "local_memory",
        "cache_size",
        "cache_linesize",
        "RSMIVRAMSize",
        "RSMIVisibleVRAMSize",
    }

    def is_numeric(value):
        """Check if a value can be converted to a number"""
        if value is None:
            return False
        try:
            float(str(value))
            return True
        except (ValueError, TypeError):
            return False

    def handle_inconsistent_values(values):
        """Handle inconsistent values by providing min/max for numeric, list for strings"""
        # Filter out None values
        valid_values = [v for v in values if v is not None]

        if not valid_values:
            return None

        if len(valid_values) == 1:
            return valid_values[0]

        # Check if all values are numeric
        numeric_values = []
        for val in valid_values:
            if is_numeric(val):
                # Convert to appropriate numeric type
                try:
                    # Try int first, then float
                    if "." not in str(val):
                        numeric_values.append(int(val))
                    else:
                        numeric_values.append(float(val))
                except (ValueError, TypeError):
                    pass

        # If all values are numeric, return min/max
        if len(numeric_values) == len(valid_values):
            return {"min": min(numeric_values), "max": max(numeric_values)}

        # For non-numeric or mixed values, return unique values as a list
        unique_values = sorted(list(set(str(v) for v in valid_values)))
        return unique_values

    def get_general_path(path):
        """Convert specific path to general pattern"""
        if not path:
            return ""

        # Split path and remove instance numbers
        parts = path.split("/")
        general_parts = []

        for part in parts:
            if part:
                # Remove instance numbers in brackets: "Machine[0]" -> "Machine"
                general_part = part.split("[")[0]
                general_parts.append(general_part)

        return "/".join(general_parts)

    for rtype, fields_to_check in resource_fields.items():
        if rtype == "OSDev":
            # For OSDev, only include entries that have GPUVendor attribute
            entries = [
                v
                for k, v in shortened_dict.items()
                if v.get("type") == rtype and "GPUVendor" in v
            ]
        else:
            entries = [v for k, v in shortened_dict.items() if v.get("type") == rtype]

        if not entries:
            continue

        result[rtype] = {"count": len(entries)}

        # Add general path if available
        if entries:
            sample_path = entries[0].get("path", "")
            general_path = get_general_path(sample_path)
            if general_path:
                result[rtype]["general_path"] = general_path

        for key in fields_to_check:
            values = [entry.get(key) for entry in entries if key in entry]

            if not values:
                continue

            # Get unique values
            unique_values = set(values)

            # Determine the key name
            if key in per_resource_fields:
                result_key = f"{key}_per_resource"
            else:
                result_key = key

            if len(unique_values) == 1:
                # All values are the same
                result[rtype][result_key] = values[0]
            else:
                # Values are inconsistent - handle with min/max or list
                result[rtype][result_key] = handle_inconsistent_values(unique_values)

    return result


def parse_lstopo_summary(
    hwloc_xml_file_path, hwloc_output_json_file_path, os_reserved_metadata
):
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

        # 4) Add resource summaries directly at top level
        resource_summaries = extract_commons(shortened_dict)
        shortened_dict.update(resource_summaries)

        # 5) Add os-reserved key_value pairs
        shortened_dict.update(os_reserved_metadata)

        # 6) Persist the json
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
    parser.add_argument("os_reserved", type=str, help="machine os_reserved information")

    args = parser.parse_args()

    parse_lstopo_summary(
        args.hwloc_xml_log_file, args.hwloc_json_log_file, json.loads(args.os_reserved)
    )
