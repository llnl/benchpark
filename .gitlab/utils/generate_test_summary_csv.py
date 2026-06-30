#!/usr/bin/env python3

import argparse
import csv
import json
import os
import re
import sys
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS_DIR = REPO_ROOT / "experiments"

# Fixed system columns. Compatibility is intentionally limited to programming models.
COLUMN_LABELS = {
    "dane": "dane (mpi/openmp)",
    "matrix": "matrix (cuda)",
    "tioga": "tioga (rocm)",
    "tuolumne": "tuolumne (rocm)",
}

SYSTEM_MODELS = {
    "dane": {"mpi", "openmp"},
    "matrix": {"mpi", "openmp", "cuda"},
    "tioga": {"mpi", "openmp", "rocm"},
    "tuolumne": {"mpi", "openmp", "rocm"},
}

EXPERIMENT_MODEL_MARKERS = {
    "ProgrammingModelType.Openmp": "openmp",
    "ProgrammingModelType.Cuda": "cuda",
    "ProgrammingModelType.Rocm": "rocm",
    "ProgrammingModelType.Mpionly": "mpi",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a benchmark summary CSV from GitLab test-stage jobs."
    )
    parser.add_argument(
        "--output",
        default="test-summary.csv",
        help="Output CSV path. Defaults to %(default)s.",
    )
    parser.add_argument(
        "--jobs-json",
        help="Optional path to a JSON file containing the pipeline jobs payload.",
    )
    parser.add_argument(
        "--stage",
        default="test",
        help="Only inspect jobs from this stage. Defaults to %(default)s.",
    )
    return parser.parse_args()


def get_env(name_a, name_b=None):
    value = os.environ.get(name_a)
    if value:
        return value
    if name_b:
        return os.environ.get(name_b)
    return None


def load_jobs_from_api():
    api_url = get_env("GITLAB_API_V4_URL", "CI_API_V4_URL")
    project_id = get_env("GITLAB_PROJECT_ID", "CI_PROJECT_ID")
    pipeline_id = get_env("CI_PIPELINE_ID")
    job_token = get_env("GITLAB_JOB_TOKEN", "CI_JOB_TOKEN")
    private_token = get_env("GITLAB_PRIVATE_TOKEN", "PRIVATE_TOKEN") or get_env(
        "GITLAB_TOKEN"
    )

    if not api_url:
        raise RuntimeError("Missing GitLab API URL.")
    if not project_id:
        raise RuntimeError("Missing GitLab project ID.")
    if not pipeline_id:
        raise RuntimeError("Missing CI_PIPELINE_ID.")
    if job_token:
        auth_header = ("JOB-TOKEN", job_token)
    elif private_token:
        auth_header = ("PRIVATE-TOKEN", private_token)
    else:
        raise RuntimeError("Missing GitLab token.")

    jobs = []
    page = 1
    while True:
        url = (
            f"{api_url}/projects/{urllib.parse.quote(str(project_id), safe='')}"
            f"/pipelines/{urllib.parse.quote(str(pipeline_id), safe='')}/jobs"
            f"?per_page=100&page={page}"
        )
        request = urllib.request.Request(url, headers={auth_header[0]: auth_header[1]})
        try:
            with urllib.request.urlopen(request) as response:
                jobs.extend(json.load(response))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Failed to query GitLab jobs: {exc}") from exc

        next_page = response.headers.get("X-Next-Page")
        if not next_page:
            break
        page = int(next_page)

    return jobs


def load_jobs(jobs_json_path=None):
    if jobs_json_path:
        with open(jobs_json_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return load_jobs_from_api()


def benchmark_names():
    return sorted(
        [
            path.name
            for path in EXPERIMENTS_DIR.iterdir()
            if path.is_dir()
        ],
        key=len,
        reverse=True,
    )


def load_experiment_models():
    command = [str(REPO_ROOT / "bin" / "benchpark"), "list", "experiments", "--no-title"]
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(
            "Unable to query experiment metadata with benchpark list experiments; "
            "falling back to experiment.py source scan.",
            file=sys.stderr,
        )
        if exc.stdout:
            print(exc.stdout, file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        return load_experiment_models_from_source()

    models_by_benchmark = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue

        match = re.match(r"^([A-Za-z0-9_.-]+)(?:\+\[([^\]]+)\])?", line)
        if not match:
            continue

        benchmark, model_group = match.groups()
        models_by_benchmark[benchmark] = (
            set(model_group.split("|")) if model_group else set()
        )

    return models_by_benchmark


def load_experiment_models_from_source():
    models_by_benchmark = {}
    for experiment_dir in EXPERIMENTS_DIR.iterdir():
        experiment_file = experiment_dir / "experiment.py"
        if not experiment_file.is_file():
            continue

        file_text = experiment_file.read_text(encoding="utf-8")
        models_by_benchmark[experiment_dir.name] = {
            model
            for marker, model in EXPERIMENT_MODEL_MARKERS.items()
            if marker in file_text
        }

    return models_by_benchmark


def extract_matrix_payload(job_name):
    match = re.search(r"\[(.*)\]", job_name)
    return match.group(1) if match else None


def find_value(payload, pattern):
    match = re.search(pattern, payload)
    return match.group(1) if match else None


def find_benchmark(payload, benchmarks):
    for benchmark in benchmarks:
        if re.search(rf"(?:^|,\s){re.escape(benchmark)}(?:,|$)", payload):
            return benchmark
    return None


def split_payload(payload):
    return [token.strip() for token in re.split(r",\s+", payload) if token.strip()]


def row_model(tokens):
    token_text = " ".join(tokens)
    for model in ("cuda", "rocm", "openmp"):
        if re.search(rf"(^|[\s+])\+{model}($|[\s~+])", token_text):
            return model
    return "mpi"


def row_spec(tokens, benchmark):
    ignored_tokens = set(COLUMN_LABELS) | {
        "llnl-cluster",
        "llnl-matrix",
        "llnl-elcapitan",
    }
    extras = []
    for token in tokens:
        if token == benchmark or token in ignored_tokens or token.startswith("$"):
            continue
        extras.append(token)
    return " ".join([benchmark] + extras)


def parse_job(job, benchmarks):
    payload = extract_matrix_payload(job["name"])
    if not payload:
        return None

    tokens = split_payload(payload)
    host = find_value(payload, r"(?:^|,\s)(dane|matrix|tuolumne|tioga)(?:,|$)")
    benchmark = find_benchmark(payload, benchmarks)
    if not host or not benchmark:
        return None

    return {
        "host": host,
        "benchmark": benchmark,
        "model": row_model(tokens),
        "row_spec": row_spec(tokens, benchmark),
        "status": job["status"],
        "name": job["name"],
    }


def cell_status(existing, job_status):
    current = "Pass" if job_status == "success" else "Fail"
    if existing == "Fail" or current == "Fail":
        return "Fail"
    return "Pass"


def build_summary_rows(jobs, stage):
    benchmarks = benchmark_names()
    experiment_models = load_experiment_models()
    rows = {}
    unparsed_jobs = []

    for job in jobs:
        if job.get("stage") != stage:
            continue
        if job.get("retried"):
            continue

        parsed = parse_job(job, benchmarks)
        if not parsed:
            unparsed_jobs.append(job["name"])
            continue

        if parsed["row_spec"] not in rows:
            supported_models = experiment_models.get(parsed["benchmark"], set())
            rows[parsed["row_spec"]] = {}
            for host, label in COLUMN_LABELS.items():
                if (
                    parsed["model"] in supported_models
                    and parsed["model"] in SYSTEM_MODELS[host]
                ):
                    rows[parsed["row_spec"]][label] = "Not Tested"
                else:
                    rows[parsed["row_spec"]][label] = "N/A"

        label = COLUMN_LABELS[parsed["host"]]
        rows[parsed["row_spec"]][label] = cell_status(
            rows[parsed["row_spec"]][label], parsed["status"]
        )

    return rows, unparsed_jobs


def write_csv(output_path, rows):
    fieldnames = ["experiment_spec"] + list(COLUMN_LABELS.values())
    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for experiment_spec in sorted(rows):
            writer.writerow(
                {"experiment_spec": experiment_spec} | rows[experiment_spec]
            )


def main():
    args = parse_args()
    jobs = load_jobs(args.jobs_json)
    rows, unparsed_jobs = build_summary_rows(jobs, args.stage)
    write_csv(args.output, rows)

    if unparsed_jobs:
        print(
            f"Skipped {len(unparsed_jobs)} test jobs that could not be parsed.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
