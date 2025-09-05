from benchpark.directives import variant, maintainers
from benchpark.paths import hardware_descriptions
from benchpark.system import System, JobQueue
from benchpark.openmpsystem import OpenMPCPUOnlySystem
from packaging.version import Version


class NerscPerlmutter(System):

    id_to_resources = {
        "perlmutter": {
            "sys_cores_per_node": 64,      # GPU node: 1×EPYC 7763, 64 cores
            "sys_cores_os_reserved_per_node": 0,
            "sys_sockets_per_node": 1,
            "sys_gpus_per_node": 0,        # set to 4 when on GPU nodes
            "system_site": "nersc",
            "scheduler": "slurm",
            "interconnect": "slingshot11",
            "hardware_key": str(hardware_descriptions)
            + "/HPECray-EPYC-Milan-A100-Slingshot/hardware_description.yaml",
            "queues": [
                JobQueue("debug", 30, 16),          # 30 min; small scale debug
                JobQueue("shared", 12 * 60, 64),    # shared QoS (CPU or GPU-shared)
                JobQueue("regular", 48 * 60, 2048), # production; node-exclusive
            ],
        }
    }

    variant(
        "gputype",
        default="none",
        values=("none", "a100-40g", "a100-80g"),
        description="GPU selection; 'none' = CPU nodes, A100 40GB or 80GB GPU nodes otherwise.",
    )

    variant(
        "queue",
        default="none",
        values=("none", "debug", "shared", "regular"),
        multi=False,
        description="Override QoS/partition selection.",
    )

    def __init__(self, spec):
        super().__init__(spec)
        self.programming_models = [OpenMPCPUOnlySystem()]

        attrs = self.id_to_resources["perlmutter"]
        for k, v in attrs.items():
            setattr(self, k, v)

        gt = self.spec.variants["gputype"][0]
        if gt == "none":
            self.sys_gpus_per_node = 0
            self.sys_cores_per_node = 128
            self.sys_sockets_per_node = 2
        elif gt in ("a100-40g", "a100-80g"):
            self.sys_gpus_per_node = 4
            self.sys_cores_per_node = 64
            self.sys_sockets_per_node = 1
        else:
            raise ValueError(f"Invalid gputype in spec: {self.spec}")

