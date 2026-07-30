# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import importlib
import pathlib
import subprocess
import sys
import types


class FakeSeries:
    def __init__(self, values):
        self.values = values

    @property
    def loc(self):
        return self

    def __getitem__(self, profile):
        return self.values[profile]


class FakeLoc:
    def __init__(self, values):
        self.values = values

    def __getitem__(self, key):
        node, metric = key
        return FakeSeries(self.values[(node, metric)])


class FakeMetadataLoc:
    def __init__(self, values):
        self.values = values

    def __getitem__(self, key):
        profile, column = key
        return self.values[(profile, column)]


class FakeMetadata:
    def __init__(self, columns, values):
        self.columns = columns
        self.loc = FakeMetadataLoc(values)


class FakeDataFrame:
    def __init__(self, values, columns):
        self.columns = columns
        self.loc = FakeLoc(values)


class FakeThicket:
    last = None

    def __init__(self):
        self.profile = ["base_hash", "new_hash"]
        self.dataframe = FakeDataFrame(
            {("main", "Avg time/rank"): {"base_hash": 10.0, "new_hash": 12.5}},
            ["Avg time/rank"],
        )
        self.metadata = FakeMetadata(
            ["Final-FOM", "packages.dependencies.hip.version"],
            {
                ("base_hash", "packages.dependencies.hip.version"): "6.4.2",
                ("new_hash", "packages.dependencies.hip.version"): "7.2.0",
            },
        )
        self.replaced_profile = None
        self.moved_metadata = None
        self.queried = False

    @classmethod
    def from_caliperreader(cls, files, disable_tqdm=False):
        cls.last = cls()
        cls.last.files = files
        cls.last.disable_tqdm = disable_tqdm
        return cls.last

    def replace_profile_index(self, column):
        self.replaced_profile = column
        self.profile = ["6.4.2", "7.2.0"]
        self.dataframe.loc.values[("main", "Avg time/rank")] = {
            "6.4.2": 10.0,
            "7.2.0": 12.5,
        }

    def metadata_columns_to_perfdata(self, column):
        self.moved_metadata = column
        self.dataframe.columns.append(column)
        self.dataframe.loc.values[("main", column)] = {
            "base_hash": 100.0,
            "new_hash": 110.0,
        }

    def get_node(self, region):
        return region

    def query(self, query):
        self.queried = True
        return self


def import_compare(monkeypatch):
    fake_thicket = types.SimpleNamespace(
        Thicket=FakeThicket,
        query=types.SimpleNamespace(
            Query=lambda: types.SimpleNamespace(
                match=lambda *args, **kwargs: "fake-query"
            )
        ),
    )
    monkeypatch.setitem(sys.modules, "thicket", fake_thicket)
    sys.modules.pop("benchpark.cmd.compare", None)
    return importlib.import_module("benchpark.cmd.compare")


def test_compare_parser_requires_region_and_metric(monkeypatch):
    compare = import_compare(monkeypatch)
    parser = argparse.ArgumentParser()
    compare.setup_parser(parser)

    args = parser.parse_args(
        ["base.cali", "new.cali", "--region", "main", "--metric", "Avg time/rank"]
    )

    assert args.base_file == "base.cali"
    assert args.compare_file == "new.cali"
    assert args.region == "main"
    assert args.metric == "Avg time/rank"


def test_compare_command_uses_default_profile_hashes(monkeypatch, capsys):
    compare = import_compare(monkeypatch)
    args = argparse.Namespace(
        base_file="base.cali",
        compare_file="new.cali",
        region="main",
        metric="Avg time/rank",
        metadata_profile_identifier=None,
        exclude_regions=None,
    )

    assert compare.command(args) == 0
    out = capsys.readouterr().out

    assert FakeThicket.last.files == ["base.cali", "new.cali"]
    assert FakeThicket.last.disable_tqdm
    assert "base_hash: 10" in out
    assert "new_hash: 12.5" in out
    assert "Change: +2.5 (+25.0%)" in out


def test_compare_command_can_relabel_profiles(monkeypatch, capsys):
    compare = import_compare(monkeypatch)
    args = argparse.Namespace(
        base_file="base.cali",
        compare_file="new.cali",
        region="main",
        metric="Avg time/rank",
        metadata_profile_identifier="packages.dependencies.hip.version",
        exclude_regions=None,
    )

    compare.command(args)
    out = capsys.readouterr().out

    assert FakeThicket.last.replaced_profile == "packages.dependencies.hip.version"
    assert "6.4.2: 10" in out
    assert "7.2.0: 12.5" in out


def test_compare_command_can_compare_metadata_metric(monkeypatch, capsys):
    compare = import_compare(monkeypatch)
    args = argparse.Namespace(
        base_file="base.cali",
        compare_file="new.cali",
        region="main",
        metric="Final-FOM",
        metadata_profile_identifier=None,
        exclude_regions=None,
    )

    compare.command(args)
    out = capsys.readouterr().out

    assert FakeThicket.last.moved_metadata == "Final-FOM"
    assert "Change: +10 (+10.0%)" in out


def test_compare_command_can_exclude_regions(monkeypatch):
    compare = import_compare(monkeypatch)
    args = argparse.Namespace(
        base_file="base.cali",
        compare_file="new.cali",
        region="main",
        metric="Avg time/rank",
        metadata_profile_identifier=None,
        exclude_regions=["MPI_"],
    )

    compare.command(args)

    assert FakeThicket.last.queried


def test_compare_help_is_registered():
    benchpark_root = pathlib.Path(__file__).resolve().parents[3]
    subprocess.run(
        [sys.executable, benchpark_root / "lib" / "main.py", "compare", "-h"],
        check=True,
        capture_output=True,
        text=True,
    )
