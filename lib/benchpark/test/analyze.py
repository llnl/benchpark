# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import re
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("hatchet")
pytest.importorskip("thicket")

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import benchpark.cmd.analyze as analyze  # noqa: E402

# Two trials of amg2023+rocm on tuolumne, also used by the query tests
CALI_DATA = Path(__file__).parent / "data" / "query"


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def _set_global(text, name, value):
    """Rewrite the value of the Caliper global attribute ``name``."""
    attribute = re.search(
        rf"^__rec=node,id=(\d+),attr=\d+,data={re.escape(name)},", text, re.M
    ).group(1)
    text, count = re.subn(
        rf"^(__rec=node,id=\d+,attr={attribute},data=)[^,]*,",
        rf"\g<1>{value},",
        text,
        flags=re.M,
    )
    assert count == 1
    return text


def _workspace(tmp_path, scaling=None, second_trial=()):
    """Copy the trials, optionally enabling a scaling variant in the recorded
    spec and overriding globals of the second trial."""
    workspace = tmp_path / "workspace"
    for index, source in enumerate(sorted(CALI_DATA.rglob("*.cali"))):
        text = source.read_text()
        if scaling:
            text = text.replace(f"~{scaling}", f"+{scaling}")
        if index == 1:
            for name, value in second_trial:
                text = _set_global(text, name, value)
        dest = workspace / source.relative_to(CALI_DATA)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
    return workspace


def _analyze(workspace, *argv):
    parser = argparse.ArgumentParser()
    analyze.setup_parser(parser)
    return analyze.command(
        parser.parse_args(["--workspace-dir", str(workspace)] + list(argv))
    )


def test_analyze_default_area_chart(tmp_path):
    workspace = _workspace(tmp_path, "strong", second_trial=[("n_resources", 8)])

    assert _analyze(workspace) == 0

    out = workspace / "analyze"
    name = "amg2023_rocm_strong_raw_exc"
    for suffix in (".png", ".csv", "-tree.txt"):
        assert (out / f"{name}{suffix}").exists()
    assert "main" in (out / f"{name}-tree.txt").read_text()
    data = pd.read_csv(out / f"{name}.csv")
    assert sorted(data["n_resources"].unique()) == [4, 8]
    assert (out / ".last-command.sh").read_text().startswith("#!/bin/bash\nbenchpark")


def test_analyze_line_chart_options(tmp_path):
    workspace = _workspace(tmp_path, "weak")

    _analyze(
        workspace,
        "--chart-kind",
        "line",
        "--chart-type",
        "percentage",
        "--top-n-regions",
        "3",
        "--no-mpi",
        "--yaxis-log",
        "--chart-figsize",
        "8",
        "5",
        "--chart-fontsize",
        "9",
        "--chart-yaxis-limits",
        "0",
        "100",
        "--chart-title",
        "AMG2023",
        "--chart-xlabel",
        "n_nodes",
        "--chart-ylabel",
        "Share of time",
        "--disable-legend",
        "--output-filename",
        "custom",
    )

    data = pd.read_csv(workspace / "analyze" / "custom.csv")
    # Three regions plus the sum of everything that was filtered out
    assert set(data["name"]) >= {"Sum(removed_regions)"}
    assert data["name"].nunique() == 4
    assert not data["name"].str.startswith("MPI_").any()
    assert (workspace / "analyze" / "custom.png").exists()


def test_analyze_bar_chart_with_grouping(tmp_path):
    workspace = _workspace(tmp_path, "throughput")

    _analyze(
        workspace,
        "--chart-kind",
        "bar",
        "--group-regions-name",
        "--exclude-regions",
        "hypre",
        "--xaxis-parameter",
        "n_nodes",
        "--normalize-by",
        "Calls/rank (max)",
    )

    data = pd.read_csv(workspace / "analyze" / "amg2023_rocm_throughput_raw_exc.csv")
    assert not data["name"].str.contains("hypre").any()
    assert data.groupby(["name", "profile"]).size().max() == 1


def test_analyze_scatter_of_selected_regions(tmp_path):
    workspace = _workspace(tmp_path, "strong")
    trial = next(workspace.rglob("*.cali")).stem.split("_")[-1]

    _analyze(
        workspace,
        "--chart-kind",
        "scatter",
        "--query-regions-byname",
        "main",
        "--filter-regions-byname",
        "main",
        "--calltree-unification",
        "intersection",
        "--file-name-match",
        trial,
    )

    data = pd.read_csv(workspace / "analyze" / "amg2023_rocm_strong_raw_exc.csv")
    assert data["profile"].nunique() == 1
    assert (data["name"] == "main").all()


def test_analyze_compares_clusters(tmp_path):
    workspace = _workspace(tmp_path, "strong", second_trial=[("cluster", "dane")])

    _analyze(workspace, "--chart-kind", "line")
    data = pd.read_csv(workspace / "analyze" / "amg2023_rocm_strong_raw_exc.csv")
    assert set(data["cluster"]) == {"tuolumne", "dane"}

    with pytest.raises(ValueError, match="not allowed for 'area' chart type"):
        _analyze(workspace)


def test_analyze_requires_scaling_experiment(tmp_path):
    with pytest.raises(ValueError, match="Unknown scaling type"):
        _analyze(_workspace(tmp_path))


def test_analyze_clean(tmp_path):
    workspace = _workspace(tmp_path, "strong")
    out = workspace / "analyze"
    (out / "old-chart").mkdir(parents=True)
    (out / "old.csv").write_text("")
    (out / ".ramble-workspace").write_text("")
    (out / "link").symlink_to(out / "old-chart")

    _analyze(workspace, "clean", "--dry-run")
    assert {p.name for p in out.iterdir()} == {
        "old-chart",
        "old.csv",
        ".ramble-workspace",
        "link",
    }

    _analyze(workspace, "clean")
    assert {p.name for p in out.iterdir()} == {".ramble-workspace"}


def test_analyze_archive(tmp_path, capsys):
    workspace = _workspace(tmp_path, "strong")
    archive = tmp_path / "results.tar.gz"

    _analyze(workspace, "archive", "--archive-output", str(archive))

    assert capsys.readouterr().out.strip() == str(archive)
    with tarfile.open(archive) as tar:
        names = tar.getnames()
    assert "analyze" in names
    assert sorted(n for n in names if n.endswith(".cali")) == sorted(
        p.name for p in workspace.rglob("*.cali")
    )

    # Without --archive-output the archive lands in the analyze dir and
    # does not include itself
    _analyze(workspace, "archive")
    default = capsys.readouterr().out.strip()
    assert Path(default).parent == workspace / "analyze"
    with tarfile.open(default) as tar:
        assert not any(n.endswith(".tar.gz") for n in tar.getnames())


def test_get_scaling_type():
    assert analyze.get_scaling_type("amg2023+rocm+weak") == "weak"
    with pytest.raises(ValueError, match="Unknown scaling type"):
        analyze.get_scaling_type("amg2023+rocm~strong")


def test_validate_single_metadata_value():
    tk = SimpleNamespace(metadata=pd.DataFrame({"version": ["1.0", "1.0"]}))
    assert analyze.validate_single_metadata_value("version", tk) == "1.0"

    tk.metadata.loc[1, "version"] = "2.0"
    with pytest.raises(ValueError, match="Expected one version"):
        analyze.validate_single_metadata_value("version", tk)


def test_validate_workspace_dir(tmp_path):
    assert analyze._validate_workspace_dir(str(tmp_path)) == str(tmp_path)
    with pytest.raises(ValueError, match="does not exist"):
        analyze._validate_workspace_dir(str(tmp_path / "missing"))


def test_derived_metrics():
    frame = pd.DataFrame(
        {
            "Total SQ_INSTS_VALU_MFMA_MOPS_BF16 (exc)": [2.0 * 10**12],
            "Max GPU time (E)": [512.0],
            "Bytes/Rep": [4.0 * 10**9],
            "Flops/Rep": [2.0 * 10**9],
            "Avg time/rank (exc)": [2.0],
            "Reps": [10],
        }
    )
    tk = SimpleNamespace(
        dataframe=frame, exc_metrics=[], metadata={"mpi.world.size": 4}
    )

    assert analyze.Application(tk).set_metrics() == ["TFLOPS (BF16)"]
    assert frame["TFLOPS (BF16)"].iloc[0] == pytest.approx(2.0)

    assert analyze.RAJAPerf(tk).set_metrics() == [
        "Memory Bandwidth (GB/s)",
        "FLOP Rate (GFLOPS)",
    ]
    assert frame["Memory Bandwidth (GB/s)"].iloc[0] == pytest.approx(80.0)
    assert frame["FLOP Rate (GFLOPS)"].iloc[0] == pytest.approx(40.0)
    assert tk.exc_metrics == [
        "TFLOPS (BF16)",
        "Memory Bandwidth (GB/s)",
        "FLOP Rate (GFLOPS)",
    ]
