#!/usr/bin/env python3

import glob

import pandas as pd
import yaml


def main():
    sysconfig_yaml_files = glob.glob(
        "../systems/all_hardware_descriptions/**/hardware_description.yaml",
        recursive=True,
    )

    df_list = []
    for f in sysconfig_yaml_files:
        with open(f, "r") as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

            tmp_df = pd.json_normalize(data, max_level=2)
            df_list.append(tmp_df)

    df = pd.concat(df_list)

    systested_columns_to_merge = [col for col in df.columns if "systems-tested" in col]
    top500_cols_to_merge = [
        col for col in df.columns if "top500-system-instances" in col
    ]

    def merge_dicts(row, merge_cols):
        combined_dict = {}
        for col in merge_cols:
            if isinstance(row[col], dict):  # Check if the value is a dictionary
                combined_dict.update(
                    {col.split(".")[-1]: row[col]}
                )  # Merge the dictionary
        return combined_dict

    df["systems-tested"] = df.apply(
        lambda row: merge_dicts(row, systested_columns_to_merge), axis=1
    )
    df["top500-system-instances"] = df.apply(
        lambda row: merge_dicts(row, top500_cols_to_merge), axis=1
    )
    df = df.drop(columns=systested_columns_to_merge + top500_cols_to_merge)

    # Remove system_definition from all field names
    # (e.g., system_definition.system-tested.description)
    df.columns = df.columns.str.removeprefix("system_definition.")

    # Replace NaN with empty string
    df.fillna("", inplace=True)

    # Set index to be field names
    df.set_index("name", inplace=True)

    # Write out current system definitions to CSV format
    df.to_csv("current-system-definitions.csv")


if __name__ == "__main__":
    main()
