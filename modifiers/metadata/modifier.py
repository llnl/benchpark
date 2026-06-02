from pathlib import Path
import json
import re
import subprocess

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

    metadata_file = "{experiment_run_dir}/version_metadata.json"
    versions_file = "checkout-versions.yaml"
    
    def extract_benchpark_version(self):
        repo_root = Path(self._file_path).resolve().parents[2]
        benchpark_hash = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            text=True,
        ).strip()
        return benchpark_hash
        
    def extract_dependencies_version(self):
        repo_root = Path(self._file_path).resolve().parents[2]

        with open(repo_root / self.versions_file, "r", encoding="utf-8") as f:
            version_data = yaml.safe_load(f)

        dependencies_ver_json = version_data.get("versions")

        return {
            "ramble": dependencies_ver_json.get("ramble"),
            "spack": dependencies_ver_json.get("spack"),
            "spack-packages": dependencies_ver_json.get("spack-packages"),
        }

    def extract_package_version(self, app_inst):
        package_name = app_inst.name

        package_ver_raw = subprocess.check_output(
            ["spack", "find", "--json", package_name],
            text=True,
        )

        package_ver_json = json.loads(package_ver_raw)[0]

        return {
            "name": package_ver_json.get("name"),
            "version": package_ver_json.get("version"),
            "commit": package_ver_json.get("parameters").get("commit"),
        }

    def write_metadata_command(self, app_inst):
        metadata = {
            "benchpark": self.extract_benchpark_version(),
            "dependencies": self.extract_dependencies_version(),
            "package": self.extract_package_version(app_inst),
        }
        escaped_json = json.dumps(metadata, indent=2).replace("'", "'\"'\"'")
        return "(printf '%s' '{}' > {})".format(escaped_json, self.metadata_file)

    def metadata(self, executable_name, executable, app_inst=None):
        from ramble.util.executable import CommandExecutable

        pre_exec = []
        post_exec = []

        caliper_modifier = any(
            [modifier["name"] == "caliper" for modifier in app_inst.modifiers]
        )

        pre_exec.append(
            CommandExecutable(
                f"write-build-info-{executable_name}",
                template=[self.write_metadata_command(app_inst)],
            )
        )

        if caliper_modifier:
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

    
