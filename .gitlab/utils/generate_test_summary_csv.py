#!/usr/bin/env python3

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS_DIR = REPO_ROOT / "experiments"

# Fixed baseline columns requested for the nightly-style summary layout.
COLUMN_SPECS = [
    ("dane", "oneapi", "mvapich2"),
    ("dane", "gcc", "mvapich2"),
    ("dane", "intel", "mvapich2"),
    ("dane", "llvm", "mvapich2"),
    ("dane", "oneapi", "openmpi"),
    ("dane", "gcc", "openmpi"),
    ("dane", "intel", "openmpi"),
    ("dane", "llvm", "openmpi"),
    ("matrix", "oneapi", "mvapich2"),
    ("matrix", "gcc", "mvapich2"),
    ("matrix", "intel", "mvapich2"),
    ("matrix", "oneapi", "openmpi"),
    ("matrix", "gcc", "openmpi"),
    ("matrix", "intel", "openmpi"),
    ("tuolumne", "cce", "cray-mpich"),
    ("tuolumne", "gcc", "cray-mpich"),
    ("tuolumne", "rocmcc", "cray-mpich"),
    ("tioga", "cce", "cray-mpich"),
    ("tioga", "gcc", "cray-mpich"),
    ("tioga", "rocmcc", "cray-mpich"),
]

COLUMN_LABELS = {
    spec: f"{spec[0]} ({spec[1]} | {spec[2]})" for spec in COLUMN_SPECS
}

DEFAULT_CONFIGS = {
    "dane": ("oneapi", "mvapich2"),
    "matrix": ("gcc", "mvapich2"),
    "tuolumne": ("cce", "cray-mpich"),
    "tioga": ("cce", "cray-mpich"),
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


def parse_job(job, benchmarks):
    payload = extract_matrix_payload(job["name"])
    if not payload:
        return None

    host = find_value(payload, r"(?:^|,\s)(dane|matrix|tuolumne|tioga)(?:,|$)")
    benchmark = find_benchmark(payload, benchmarks)
    if not host or not benchmark:
        return None

    compiler = find_value(payload, r"(?:^|,\s)compiler=([A-Za-z0-9_-]+)(?:,|$)")
    mpi = find_value(payload, r"(?:^|,\s)mpi=([A-Za-z0-9_-]+)(?:,|$)")

    default_compiler, default_mpi = DEFAULT_CONFIGS[host]
    return {
        "host": host,
        "benchmark": benchmark,
        "compiler": compiler or default_compiler,
        "mpi": mpi or default_mpi,
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
    rows = {}
    unparsed_jobs = []
    unmapped_jobs = []

    for job in jobs:
        if job.get("stage") != stage:
            continue
        if job.get("retried"):
            continue

        parsed = parse_job(job, benchmarks)
        if not parsed:
            unparsed_jobs.append(job["name"])
            continue

        if parsed["benchmark"] not in rows:
            rows[parsed["benchmark"]] = {
                label: "N/A" for label in COLUMN_LABELS.values()
            }

        column_key = (parsed["host"], parsed["compiler"], parsed["mpi"])
        if column_key not in COLUMN_LABELS:
            unmapped_jobs.append(parsed["name"])
            continue

        label = COLUMN_LABELS[column_key]
        rows[parsed["benchmark"]][label] = cell_status(
            rows[parsed["benchmark"]][label], parsed["status"]
        )

    return rows, unparsed_jobs, unmapped_jobs


def write_csv(output_path, rows):
    fieldnames = ["benchmark"] + [COLUMN_LABELS[spec] for spec in COLUMN_SPECS]
    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for benchmark in sorted(rows):
            writer.writerow({"benchmark": benchmark} | rows[benchmark])


def main():
    args = parse_args()
    jobs = load_jobs(args.jobs_json)
    rows, unparsed_jobs, unmapped_jobs = build_summary_rows(jobs, args.stage)
    write_csv(args.output, rows)

    if unparsed_jobs:
        print(
            f"Skipped {len(unparsed_jobs)} test jobs that could not be parsed.",
            file=sys.stderr,
        )
    if unmapped_jobs:
        print(
            f"Skipped {len(unmapped_jobs)} parsed test jobs with no fixed summary column.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
