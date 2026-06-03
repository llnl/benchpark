from pathlib import Path
from ramble.modkit import *

class Hash(BasicModifier):
    """Define a modifier for collecting experiment hash metadata"""

    name = "hash"

    maintainers("vining1")
    
    mode(
        name="on",
        description="Collect experiment hash metadata and attach it to Caliper output if Caliper is present",
    )
    
    default_mode("on")

    executable_modifier("hash")
    
    def hash(self, executable_name, executable, app_inst=None):
        from ramble.util.executable import CommandExecutable

        script_dir = Path(self._file_path).resolve().parent
        hash_metadata_file_path = "{experiment_run_dir}/hash_metadata.json"
        repo_root = Path(self._file_path).resolve().parents[2]

        application_name = app_inst.name

        pre_exec = []
        post_exec = []

        pre_exec.append(
            CommandExecutable(
                f"write-json-{executable_name}",
                template=[
                    f"python {script_dir}/hash_collector.py {hash_metadata_file_path} {repo_root} {application_name}"
                ],
            )
        )

        caliper_modifier = any(
            [modifier["name"] == "caliper" for modifier in app_inst.modifiers]
        )

        if caliper_modifier:
            pre_exec.append(
                CommandExecutable(
                    f"modify-caliper-config-{executable_name}",
                    template=[
                        'export CALI_CONFIG="$CALI_CONFIG,metadata(file={})"'.format(
                            hash_metadata_file_path
                        )
                    ],
                )
            )

        return pre_exec, post_exec

    
