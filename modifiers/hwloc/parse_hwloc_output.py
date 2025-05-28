import json
import xmltodict
import argparse
from pathlib import Path


def parse_lstopo_summary(file_path):
    with open(file_path) as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
        json_data = json.dumps(data_dict, indent=2)

    output_file = Path(file_path).with_suffix(".json")
    with open(output_file, "w") as json_file:
        json_file.write(json_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="hwloc output to JSON")
    parser.add_argument("hwloc_log_file", type=str, help="hwloc output file (text)")
    parser.add_argument("mode", type=str, help="hwloc mode(text)")

    args = parser.parse_args()
    parse_lstopo_summary(args.hwloc_log_file)
