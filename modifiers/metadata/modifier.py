from pathlib import Path
import json
import subprocess
from shlex import quote

import yaml

from ramble.modkit import *


class Metadata(BasicModifier):
    """Define a modifier for collecting run metadata"""

    name = "metadata"

    maintainers("vining1")
    
    mode(
        name="on",
        description="Collect build metadata and attach it to Caliper output",
    )
    
    default_mode("on")

    executable_modifier("metadata")

    metadata_file = "{experiment_run_dir}/build_info.json"
    versions_file = "checkout-versions.yaml"

    def extract_version_metadata(self):
        repo_root = Path(self._file_path).resolve().parents[2]

        with open(repo_root / self.versions_file, "r", encoding="utf-8") as f:
            version_data = yaml.safe_load(f) or {}

        versions = dict(version_data.get("versions", {}))

        benchpark_hash = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            text=True,
        ).strip()

        versions["benchpark"] = benchpark_hash

        return json.dumps({"versions": versions})

    def write_metadata_command(self):
        escaped_json = self.extract_version_metadata().replace("'", "'\"'\"'")
        return "(printf '%s' '{}' > {})".format(escaped_json, self.metadata_file)


    def metadata(self, executable_name, executable, app_inst=None):
        from ramble.util.executable import CommandExecutable

        pre_exec = []
        post_exec = []

        caliper_modifier = any(
            [modifier["name"] == "caliper" for modifier in app_inst.modifiers]
        )

        if caliper_modifier:
            pre_exec.append(
                CommandExecutable(
                    f"write-build-info-{executable_name}",
                    template=[self.write_metadata_command()],
                )
            )

            pre_exec.append(
                CommandExecutable(
                    f"modify-caliper-config-{executable_name}",
                    template=[
                        'export CALI_CONFIG="$CALI_CONFIG,metadata(file={})"'.format(
                            self.metadata_file
                        )
                    ],
                )
            )

        return pre_exec, post_exec

    
