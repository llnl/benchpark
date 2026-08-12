# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import csv
import importlib
import pathlib
import sys

import pytest

QUERY_DATA = pathlib.Path(__file__).parent / "data" / "query"
AMG2023_ROCM642_TUO_PROBLEM1 = (QUERY_DATA / "rocm642-tuo-amg2023-problem1").resolve()


class FakeDatetime:
    @classmethod
    def now(cls):
        return cls()

    def strftime(self, fmt):
        return "01234567-012345"


def import_query(monkeypatch):
    sys.modules.pop("benchpark.cmd.query", None)
    query = importlib.import_module("benchpark.cmd.query")
    monkeypatch.setattr(query, "datetime", FakeDatetime)
    return query


def test_query_parser_requires_directories_and_metric(monkeypatch):
    query = import_query(monkeypatch)
    parser = argparse.ArgumentParser()
    query.setup_parser(parser)

    args = parser.parse_args(
        [
            str(AMG2023_ROCM642_TUO_PROBLEM1),
            "--metric",
            "Avg time/rank",
            "--query-regions-byname",
            "main",
            "--metadata-columns",
            "n_nodes",
        ]
    )

    assert args.directories == [str(AMG2023_ROCM642_TUO_PROBLEM1)]
    assert args.metric == "Avg time/rank"
    assert args.query_regions_byname == ["main"]
    assert args.metadata_columns == ["n_nodes"]


def test_query_command_reads_real_caliper_data(monkeypatch, tmp_path, capsys):
    query = import_query(monkeypatch)
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(
        directories=[str(AMG2023_ROCM642_TUO_PROBLEM1)],
        query_regions_byname=["main"],
        filter_regions_byname=[],
        metric="Avg time/rank",
        metadata_columns=[],
        exclude_regions=None,
    )

    assert query.command(args) == 0
    out = capsys.readouterr().out

    csv_path = tmp_path / "query-01234567-012345.csv"
    assert out == f"{csv_path.name}\n"
    assert csv_path.exists()

    with csv_path.open(newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 2
    assert {row["cluster"] for row in rows} == {"tuolumne"}
    assert {row["application_name"] for row in rows} == {"amg2023"}
    assert [float(row["Avg time/rank"]) for row in rows] == pytest.approx(
        [
            62.07430117410001,
            63.49193220765,
        ]
    )


def test_query_command_includes_final_fom_metadata_column(
    monkeypatch, tmp_path, capsys
):
    query = import_query(monkeypatch)
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(
        directories=[str(AMG2023_ROCM642_TUO_PROBLEM1)],
        query_regions_byname=["main"],
        filter_regions_byname=[],
        metric="Avg time/rank",
        metadata_columns=["Final-FOM"],
        exclude_regions=None,
    )

    assert query.command(args) == 0
    out = capsys.readouterr().out

    csv_path = tmp_path / "query-01234567-012345.csv"
    assert out == f"{csv_path.name}\n"

    with csv_path.open(newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert list(rows[0].keys()) == [
        "cluster",
        "application_name",
        "Final-FOM",
        "Avg time/rank",
    ]
    assert [float(row["Final-FOM"]) for row in rows] == pytest.approx(
        [
            1263870000.0,
            1140180000.0,
        ]
    )


def test_query_command_requires_region_selector_for_real_perf_metric(monkeypatch):
    query = import_query(monkeypatch)
    args = argparse.Namespace(
        directories=[str(AMG2023_ROCM642_TUO_PROBLEM1)],
        query_regions_byname=[],
        filter_regions_byname=[],
        metric="Avg time/rank",
        metadata_columns=[],
        exclude_regions=None,
    )

    with pytest.raises(ValueError, match="Must provide --query-regions-byname"):
        query.command(args)
