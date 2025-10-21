#!/usr/bin/env python3

import subprocess
import sys

import pandas as pd
import yaml

sys.path.append("../lib/")
import benchpark.accounting  # noqa: E402
import benchpark.paths  # noqa: E402


def construct_tag_groups(tag_groups, tag_dicts, dictionary):
    # everything is a dict
    for k, v in dictionary.items():
        if isinstance(v, list):
            tag_groups.append(k)
            tag_dicts[k] = v
        else:
            print("ERROR in construct_tag_groups")


def main():
    benchmarks = benchpark.accounting.benchpark_benchmarks()

    f = "../taxonomy.yaml"
    with open(f, "r") as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    tag_groups = []
    tag_dicts = {}
    for k, v in data.items():
        if k == "benchpark-tags":
            construct_tag_groups(tag_groups, tag_dicts, v)
        else:
            print("ERROR in top level construct_tag_groups")

    main_dict = dict()

    tags_taggroups = {}
    for bmark in benchmarks:
        tags_taggroups[bmark] = {}
        for k, v in tag_dicts.items():
            tags_taggroups[bmark][k] = []

    for bmark in benchmarks:
        # call benchpark tags -a bmark workspace
        cmd = ["../bin/benchpark", "tags", "-a", bmark]
        try:
            byte_data = subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed cmd: {cmd}\nOutput: {e.stdout}\nError: {e.stderr}")
            raise
        tags = str(byte_data.stdout, "utf-8")
        tags = (
            tags.replace("[", "")
            .replace("]", "")
            .replace("'", "")
            .replace(" ", "")
            .replace("\n", "")
            .split(",")
        )
        for t in tags:
            for k, v in tag_dicts.items():
                if t in v:
                    tags_taggroups[bmark][k].append(t)
        main_dict[bmark] = tags_taggroups[bmark]

    # Get benchmarks that have caliper enabled
    cali_benchmarks = subprocess.run(
        [
            "../bin/benchpark",
            "list",
            "modifiers",
            "--no-title",
        ],
        check=True,
        capture_output=True,
    )
    cali_bm_str = str(cali_benchmarks.stdout, "utf-8")
    cali_bm = cali_bm_str.replace(" ", "").split("\n")
    result = []
    for item in cali_bm[cali_bm.index("caliper") + 1 :]:
        if item.startswith("\t"):
            result.append(item.strip())
        else:
            break
    cali_bm = result
    # Get available programming models for each benchmark
    pmodels_cmd = subprocess.run(
        [
            "../bin/benchpark",
            "list",
            "experiments",
            "--no-title",
        ],
        check=True,
        capture_output=True,
    )
    pmodels_str = str(pmodels_cmd.stdout, "utf-8")
    pmodels = pmodels_str.replace(" ", "").replace("\t", "").split("\n")
    # Get scaling experiments
    scaling_cmd = subprocess.run(
        [
            "../bin/benchpark",
            "list",
            "experiments",
            "--experiment",
            "weak",
            "strong",
            "throughput",
            "--no-title",
        ],
        check=True,
        capture_output=True,
    )
    scaling_str = str(scaling_cmd.stdout, "utf-8")
    scaling = scaling_str.replace(" ", "").replace("\t", "").split("\n")
    for bmark in benchmarks:
        if bmark in cali_bm:
            main_dict[bmark]["instrumented-caliper"] = True
        else:
            main_dict[bmark]["instrumented-caliper"] = False
    for bmark in benchmarks:
        main_dict[bmark]["programming-model"] = []
        main_dict[bmark]["scaling-experiments"] = []
    for bmark in benchmarks:
        if any([bmark in p for p in pmodels]):
            for expr in pmodels:
                if bmark in expr:
                    for p in ["openmp", "mpi", "cuda", "rocm"]:
                        if p in expr:
                            main_dict[bmark]["programming-model"].append(p)
        if any([bmark in s for s in scaling]):
            for expr in scaling:
                if bmark in expr:
                    for s in ["strong", "weak", "throughput"]:
                        if s in expr:
                            main_dict[bmark]["scaling-experiments"].append(s)

    df = pd.DataFrame(main_dict)
    df.to_csv("benchmark-list.csv")

    #################
    # Tables
    # columns: benchmarks (i.e., amg2023)
    # rows: tag groups (i.e., application domain).  Each cell should hopefully have a tag - and some might have multiple


if __name__ == "__main__":
    main()
