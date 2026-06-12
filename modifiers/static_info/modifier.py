import json

from ramble.modkit import *

class StaticInfo(BasicModifier):
    """Define a modifier for static compiler LLVM Plugins"""

    name = "static_info"

    # tags("profiler", "performance-analysis")

    maintainers("yejashi")
