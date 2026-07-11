from ramble.appkit import *


class Xsbench(ExecutableApplication):
    name = "xsbench"

    executable(
        "history",
        "XSBench -m history -s {benchmark_size} -G {grid_type} -p {particles} -l {lookups} -k {kernel}",
        use_mpi=False,
    )
    executable(
        "event",
        "XSBench -m event -s {benchmark_size} -G {grid_type} -l {lookups} -k {kernel}",
        use_mpi=False,
    )

    workload("history", executables=["history"])
    workload("event", executables=["event"])

    workload_variable(
        "benchmark_size",
        default="large",
        values=["small", "large", "XL", "XXL"],
        description="XSBench H-M benchmark size",
        workloads=["history", "event"],
    )
    workload_variable(
        "grid_type",
        default="unionized",
        values=["unionized", "nuclide", "hash"],
        description="Energy-grid search method",
        workloads=["history", "event"],
    )
    workload_variable(
        "particles",
        default="500000",
        description="Number of particle histories",
        workload="history",
    )
    workload_variable(
        "lookups",
        default="34",
        description="Cross-section lookups per particle in history mode",
        workloads=["history", "event"],
    )
    workload_variable(
        "kernel",
        default="0",
        description="XSBench kernel implementation ID",
        workloads=["history", "event"],
    )

    figure_of_merit(
        "Runtime",
        fom_regex=r"Runtime:\s+(?P<runtime>[0-9.]+)\s+seconds",
        group_name="runtime",
        units="s",
    )

    figure_of_merit(
        "Lookups per second",
        fom_regex=r"Lookups/s:\s+(?P<lookups_per_second>[0-9,]+)",
        group_name="lookups_per_second",
        units="lookups/s",
        fom_type=FomType.THROUGHPUT,
    )
