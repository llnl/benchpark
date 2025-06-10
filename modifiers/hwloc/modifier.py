# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from ramble.modkit import *


class Hwloc(BasicModifier):
    """Define a modifier for showing the underlying infrastructure topology"""

    name = "hwloc"

    maintainers("amroakmal")

    mode(
        name="on",
        description="Mode for executing hwloc command",
    )

    executable_modifier("hwloc")

    def hwloc(self, executable_name, executable, app_inst=None):
        import os
        from ramble.util.executable import CommandExecutable

        hwloc_parser_dir = os.path.dirname(f"{self._file_path}")
        hwloc_output_xml_file = f"{{experiment_run_dir}}/hwloc.{self._usage_mode}.xml"
        hwloc_output_json_file = Path(hwloc_output_xml_file).with_suffix(".json")

        pre_exec = []
        post_exec = []

        pre_exec.append(
            CommandExecutable(
                name="record_start_time", template=["start_time=$(date +%s%N)"]
            )
        )

        # Run the hwloc tool and save its output in XML format to a file
        pre_exec.append(
            CommandExecutable(
                "lstopo-to-get-underlying-infrastructure",
                template=[
                    f"lstopo --of xml --whole-system --whole-io --verbose {hwloc_output_xml_file} 2> /dev/null"
                ],
            )
        )

        caliper_modifier = any(
            [modifier["name"] == "caliper" for modifier in app_inst.modifiers]
        )
        if caliper_modifier:
            # Convert the .xml file from hwloc output to equivalent .json format
            pre_exec.append(
                CommandExecutable(
                    "parse-lstopo-output",
                    template=[
                        f"python {hwloc_parser_dir}/parse_hwloc_output.py {hwloc_output_xml_file} {hwloc_output_json_file} {self._usage_mode}"
                    ],
                )
            )

            pre_exec.append(
                CommandExecutable(
                    name="record_end_time", template=["end_time=$(date +%s%N)"]
                )
            )

            pre_exec.append(
                CommandExecutable(
                    name="print_elapsed_time",
                    template=[
                        'echo "Elapsed time: $((end_time - start_time)) Nanoseconds"'
                    ],
                )
            )

            # Modify Caliper config to track this json as part of its metadata
            pre_exec.append(
                CommandExecutable(
                    f"modify-caliper-config-{executable_name}",
                    template=[
                        'export CALI_CONFIG="$CALI_CONFIG,metadata(file={})"'.format(
                            hwloc_output_json_file
                        )
                    ],
                )
            )

        return pre_exec, post_exec
