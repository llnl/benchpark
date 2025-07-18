import subprocess
import time
import sys

def main():

    try:
        expr_cmd = subprocess.run(
            [
                "./bin/benchpark",
                "list",
                "experiments",
                "--no-title",
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

    mpi_only_expr = set()
    cuda_expr = []
    rocm_expr = []
    openmp_expr = []
    strong_expr = []
    weak_expr = []
    throughput_expr = []

    for e in experiments:
        name = e.split("+")[0]
        mpi_only_expr.add(name)
        
        if "cuda" in e:
            cuda_expr.append(name)
        elif "rocm" in e:
            rocm_expr.append(name)
        elif "openmp" in e:
            openmp_expr.append(name)
        
        elif "strong" in e:
            strong_expr.append(name)
        elif "weak" in e:
            weak_expr.append(name)
        elif "throughput" in e:
            throughput_expr.append(name)
    
    sys_dict = {}
    try:
        sys_dict["mpi"] = subprocess.run(
            [
                "./bin/benchpark",
                "list",
                "systems",
                "--no-title",
            ],
            capture_output=True,
            check=True,
        )
        for pmodel in ["cuda", "rocm", "openmp"]:
            sys_dict[pmodel] = subprocess.run(
                [
                    "./bin/benchpark",
                    "list",
                    "systems",
                    "--no-title",
                    "-p",
                    pmodel,
                ],
                capture_output=True,
                check=True,
            )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Output: {e.stdout}\nError: {e.stderr}")
    str_dict = {}
    for key in sys_dict:
        temp_str = str(sys_dict[key].stdout, "utf-8")
        str_dict[key] = [i for i in temp_str.replace(" "*4, "").replace("\t", "").split("\n") if i != ""]

    exprs_to_sys = [
        (mpi_only_expr, str_dict["mpi"]),
        (cuda_expr, str_dict["cuda"]),
        (rocm_expr, str_dict["rocm"]),
        (openmp_expr, str_dict["openmp"]),
        (strong_expr, str_dict["mpi"]),
        (weak_expr, str_dict["mpi"]),
        (throughput_expr, str_dict["mpi"]),
    ]

    # Calculate total number of tests before running
    total_tests = sum(len(expr_spec_list) * len(sys_spec_list) for expr_spec_list, sys_spec_list in exprs_to_sys)
    print(f"Total tests to run: {total_tests}")

    start = time.time()
    errors = {}
    fail_tests = 0
    total_tests = 0
    for expr_spec_list, sys_spec_list in exprs_to_sys:
        for espec in expr_spec_list:
            for sspec in sys_spec_list:
                total_tests += 1
                print(f"Running '{espec}' '{sspec}'")
                try:
                    cmd = f'source .github/workflows/dryrun.sh "{sspec}" "{espec}"'
                    result = subprocess.run(
                        ["bash", "-c", cmd],
                        capture_output=True,
                        check=True,
                    )
                except subprocess.CalledProcessError as e:
                    errors[f"{espec} {sspec}"] = e.stderr.decode()
                    fail_tests += 1
    end = time.time()
    print(f"Elapsed: {(end-start)/60:.2f} minutes")
    
    print(f"{total_tests-fail_tests} Passing. {fail_tests} Failling.")
    for key, value in errors.items():
        print(key)
        print(value)
    
    if fail_tests > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()