import subprocess
import json


# Original dictionary
data = {
    "openmp": {"benchmark_spec": [], "system_spec": ["llnl-cluster cluster=ruby"]},
    "cuda": {"benchmark_spec": [], "system_spec": ["llnl-sierra"]},
    "rocm": {"benchmark_spec": [], "system_spec": ["llnl-elcapitan cluster=tioga"]},
    "weak": {"benchmark_spec": [], "system_spec": ["generic-x86"]},
    "strong": {"benchmark_spec": [], "system_spec": ["generic-x86"]},
    "single_node": {"benchmark_spec": [], "system_spec": ["generic-x86"]},
    "throughput": {"benchmark_spec": [], "system_spec": ["generic-x86"]},
}


def main():
    try:
        expr_cmd = subprocess.run(
            [
                "./bin/benchpark",
                "list",
                "experiments",
            ],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Output: {e.stdout}\nError: {e.stderr}")
    expr_str = str(expr_cmd.stdout, "utf-8")
    experiments = expr_str.replace(" ", "").replace("\t", "").split("\n")
    experiments = [
        item for item in experiments if "+" in item
    ]

    for expr in experiments:
        name, mode = expr.split("+")
        data[mode]["benchmark_spec"].append(expr)

    with open("matrix.json", "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    main()
