from benchpark.directives import variant, maintainers
from benchpark.paths import hardware_descriptions
from benchpark.system import System, JobQueue
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from packaging.version import Version

class TamuGrace(System):
    id_to_resources = {
        "cpu": {
            "sys_cores_per_node": 48,
            "sys_cores_os_reserved_per_node": 0,
            "sys_sockets_per_node": 2,
            "sys_gpus_per_node": 0,
            "system_site": "tamu-hprc",
            "scheduler": "slurm",
            "interconnect": "hdr100",
            "hardware_key": str(hardware_descriptions)
            + "/Dell-Intel-CascadeLake-NVIDIA-HDR100/hardware_description.yaml",
            "queues": [
                JobQueue("short", 2 * 60, 32),       # 2 hours, up to 32 nodes
                JobQueue("medium", 24 * 60, 128),    # 1 day, up to 128 nodes
                JobQueue("long", 7 * 24 * 60, 64),   # 7 days, up to 64 nodes
                JobQueue("xlong", 21 * 24 * 60, 32), # 21 days, up to 32 nodes
            ],
        },
        "gpu": {
            "sys_cores_per_node": 48,
            "sys_cores_os_reserved_per_node": 0,
            "sys_sockets_per_node": 2,
            "sys_gpus_per_node": None,  # determined by 'gputype' variant
            "system_site": "tamu-hprc",
            "scheduler": "slurm",
            "interconnect": "hdr100",
            "hardware_key": str(hardware_descriptions)
            + "/Dell-Intel-CascadeLake-NVIDIA-HDR100/hardware_description.yaml",
            "queues": [
                JobQueue("gpu", 4 * 24 * 60, 32),      # 4 days, up to 32 nodes
                JobQueue("short", 2 * 60, 32),
                JobQueue("medium", 24 * 60, 128),
                JobQueue("long", 7 * 24 * 60, 64),
                JobQueue("xlong", 21 * 24 * 60, 32),
                JobQueue("gpu-a40", 4 * 24 * 60, 32),
            ],
        },
    }

    variant(
        "gputype",
        default="none",
        values=("none", "a100", "rtx6000", "t4", "a40"),
        description="Select GPU type; 'none' yields CPU-only nodes.",
    )

    variant(    #may not need this
        "queue",
        default="none",
        values=("none", "short", "medium", "long", "xlong", "gpu", "gpu-a40"),
        multi=False,
        description="Submit to a specific Slurm partition.",
    )

    def __init__(self, spec):
        super().__init__(spec)

        self.programming_models = [OpenMPCPUOnlySystem()]

        attrs = self.id_to_resources["grace"]
        for k, v in attrs.items():
            setattr(self, k, v)

        gt = self.spec.variants["gputype"][0]
        if gt == "none":
            self.sys_gpus_per_node = 0
        elif gt == "a100":
            self.sys_gpus_per_node = 2
        elif gt == "rtx6000":
            self.sys_gpus_per_node = 2
        elif gt == "t4":
            self.sys_gpus_per_node = 4
        elif gt == "a40":
            self.sys_gpus_per_node = 2
        else:
            raise ValueError(f"Invalid gputype in spec: {self.spec}")