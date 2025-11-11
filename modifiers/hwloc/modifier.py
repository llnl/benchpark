# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from ramble.modkit import *


class Hwloc(BasicModifier):
    """Define a modifier for showing the hardware architecture"""

    name = "hwloc"

    maintainers("amroakmal")

    mode(
        name="on",
        description="Mode for executing hwloc command",
    )

    executable_modifier("hwloc")

    def get_os_reserved_data(self, app_inst):
        import json

        system_metadata = [
            "sys_cores_per_node",  # required
            "scheduler",  # required
            "rocm_arch",
            "cuda_arch",
            "sys_cores_os_reserved_per_node",
            "sys_cores_os_reserved_per_node_list",
            "sys_gpus_per_node",
            "sys_mem_per_node_GB",
            "system_site",
        ]
        os_reserved_metadata = {}

        for key in system_metadata:
            # Certain keys not required or may not be present
            if key in app_inst.variables.keys():
                os_reserved_metadata[key] = app_inst.variables[key]

        return f"'{json.dumps(os_reserved_metadata)}'"

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
                "lstopo-to-get-hardware-architecture",
                template=[
                    f"(lstopo --of xml --whole-system --whole-io --verbose > {hwloc_output_xml_file} 2> /dev/null)"
                ],
            )
        )

        caliper_modifier = any(
            [modifier["name"] == "caliper" for modifier in app_inst.modifiers]
        )
        if caliper_modifier:
            os_reserved_metadata = self.get_os_reserved_data(app_inst)
            pre_exec.append(
                CommandExecutable(
                    "parse-lstopo-output",
                    template=[
                        f"python {hwloc_parser_dir}/parse_hwloc_output.py {hwloc_output_xml_file} {hwloc_output_json_file} {self._usage_mode} {os_reserved_metadata}"
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
