# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import xmltodict
import json

def parse_lstopo_summary(hwloc_xml_file_path, hwloc_json_file_path):
    with open(hwloc_xml_file_path) as xml_file:
        try:
            data_dict = xmltodict.parse(xml_file.read())
            json_data = json.dumps(data_dict)
            
            with open(hwloc_json_file_path, "w") as json_file:
                json_file.write(json_data)

        except Exception as e:
            raise ValueError(f"Failed to convert Hwloc XML to JSON: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="hwloc output to JSON")
    parser.add_argument("hwloc_xml_log_file", type=str, help="hwloc output in xml format")
    parser.add_argument("hwloc_json_log_file", type=str, help="hwloc output in json format")
    parser.add_argument("mode", type=str, help="hwloc mode(text)")

    args = parser.parse_args()
    parse_lstopo_summary(args.hwloc_log_file, args.hwloc_json_log_file)
