#!/usr/bin/env python3

import pandas as pd
import yaml
import sys
import subprocess

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

    main = dict()

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
                    print("appending", t, "at key", k)
                    tags_taggroups[bmark][k].append(t)
        main[bmark] = tags_taggroups[bmark]

    df = pd.DataFrame(main)
    df.to_csv("benchmark-list.csv")

    #################
    # Tables
    # columns: benchmarks (i.e., amg2023)
    # rows: tag groups (i.e., application domain).  Each cell should hopefully have a tag - and some might have multiple


if __name__ == "__main__":
    main()
