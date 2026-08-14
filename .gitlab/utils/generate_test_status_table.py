#!/usr/bin/env python3

import argparse
import json
import os
import tempfile
import textwrap
from pathlib import Path

matplotlib_cache = Path(tempfile.gettempdir()) / "matplotlib-cache"
matplotlib_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_cache))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


STATUS_ORDER = {
    "Unknown": 0,
    "Run": 0,
    "Build": 1,
    "Perf": 2,
    "Pass": 3,
}

STATUS_STYLES = {
    "Pass": {
        "label": "Passing",
        "facecolor": "#d8f5e8",
        "edgecolor": "#6bd0aa",
        "hatch": "||",
    },
    "Build": {
        "label": "Build failure",
        "facecolor": "#ffd9b8",
        "edgecolor": "#f0a25d",
        "hatch": "\\\\\\\\",
    },
    "Run": {
        "label": "Runtime failure",
        "facecolor": "#ffd6e5",
        "edgecolor": "#f0a7c5",
        "hatch": "////",
    },
    "Unknown": {
        "label": "Missing metadata",
        "facecolor": "#ece3ff",
        "edgecolor": "#b9a2e8",
        "hatch": "xx",
    },
    "Perf": {
        "label": "Perf regression",
        "facecolor": "#cfeeff",
        "edgecolor": "#8ecae6",
        "hatch": "---",
    },
    "Not Tested": {
        "label": "Not Tested",
        "facecolor": "#ffffff",
        "edgecolor": "#d0d0d0",
        "hatch": "",
    },
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a CI experiment status table image from summary JSON."
    )
    parser.add_argument("summary_json", help="Path to test_metadata_summary.json.")
    return parser.parse_args()


def load_summary(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_status(status):
    if status in STATUS_ORDER:
        return status
    return "Not Tested"


def merge_cell(existing, result):
    status = normalize_status(result.get("status"))
    changes = result.get("changes") or {}
    performance = result.get("performance") or {}
    marker_set = set(existing.get("markers", [])) if existing else set()

    if status == "Pass" and performance.get("regressed"):
        status = "Perf"

    if changed_packages(result):
        marker_set.add("dep")

    if changes.get("system_spec_changed"):
        marker_set.add("sys")

    if changes.get("experiment_spec_changed"):
        marker_set.add("exp")

    if changes.get("application_spec_changed"):
        marker_set.add("app")

    if (
        result.get("status_changed")
        or changes.get("status_changed")
        or performance.get("regression_changed")
    ):
        marker_set.add("!")

    if not existing:
        return {"status": status, "markers": sorted(marker_set)}

    existing_status = existing["status"]
    if STATUS_ORDER.get(status, 99) < STATUS_ORDER.get(existing_status, 99):
        existing_status = status

    return {"status": existing_status, "markers": sorted(marker_set)}


def result_config(result):
    parts = []
    for key in ("variant", "system_args"):
        value = (result.get(key) or "").strip()
        if value:
            parts.append(value)

    benchmark_version = (result.get("benchmark_version") or "").strip()
    if benchmark_version:
        parts.append(f"version={benchmark_version}")

    return " ".join(parts)


def row_key(result):
    return (
        result.get("benchmark") or "",
        result_config(result),
    )


def config_sort_key(config):
    return (config != "", config)


def wrap_config(config):
    if not config:
        return []
    return textwrap.wrap(config, width=34, break_long_words=False)


def build_matrix(results):
    matrix = {}
    rows = set()
    hosts = set()

    for result in results:
        benchmark = result.get("benchmark")
        host = result.get("host")
        if not benchmark or not host:
            continue

        key = row_key(result)
        rows.add(key)
        hosts.add(host)
        matrix.setdefault(key, {})
        matrix[key][host] = merge_cell(matrix[key].get(host), result)

    sorted_rows = sorted(rows, key=lambda item: (item[0], config_sort_key(item[1])))
    return sorted_rows, sorted(hosts), matrix


def marker_text(markers):
    ordered = [
        marker
        for marker in ("dep", "sys", "exp", "app", "!")
        if marker in markers
    ]
    return " ".join(ordered)


def changed_packages(result):
    changes = result.get("changes") or {}
    packages = changes.get("packages") or []
    return {
        package.get("name")
        for package in packages
        if package.get("name")
    }


def add_cell(ax, x, y, width, height, status, markers=None):
    style = STATUS_STYLES[status]
    ax.add_patch(
        Rectangle(
            (x, y),
            width,
            height,
            facecolor=style["facecolor"],
            edgecolor=style["edgecolor"],
            hatch=style["hatch"],
            linewidth=0.0,
        )
    )
    text = marker_text(markers or [])
    if text:
        ax.text(
            x + width / 2,
            y + height / 2,
            text,
            ha="center",
            va="center",
            fontsize=10,
            color="black",
        )


def render_table(summary, output_path):
    results = summary.get("results", [])
    rows, hosts, matrix = build_matrix(results)

    if not rows:
        rows = [("No Results", "")]
    if not hosts:
        hosts = ["system"]

    benchmark_width = 3.45
    cell_width = 1.45
    header_height = 0.82
    title_height = 0.62
    legend_height = 2.4
    margin = 0.25

    table_width = benchmark_width + cell_width * len(hosts)
    content_width = max(table_width, 5.8)
    row_infos = [
        {
            "benchmark": benchmark,
            "config": config,
            "config_lines": wrap_config(config),
        }
        for benchmark, config in rows
    ]
    row_heights = [
        0.42 if not row["config_lines"] else 0.35 + 0.17 * len(row["config_lines"])
        for row in row_infos
    ]

    table_height = header_height + sum(row_heights)
    total_width = content_width + margin * 2
    total_height = title_height + table_height + legend_height + margin * 2

    fig, ax = plt.subplots(figsize=(total_width, total_height), dpi=160)
    ax.set_xlim(0, total_width)
    ax.set_ylim(0, total_height)
    ax.axis("off")

    left = margin
    table_left = left + (content_width - table_width) / 2
    top = total_height - margin
    title_y = top - 0.25
    table_top = top - title_height
    header_bottom = table_top - header_height
    table_bottom = header_bottom - sum(row_heights)

    ax.text(
        left + content_width / 2,
        title_y,
        "CI Experiment Status",
        ha="center",
        va="center",
        fontsize=14,
        fontfamily="serif",
    )

    ax.plot(
        [table_left, table_left + table_width],
        [table_top, table_top],
        color="black",
        lw=0.8,
    )
    ax.plot(
        [table_left, table_left + table_width],
        [header_bottom, header_bottom],
        color="black",
        lw=0.45,
    )
    ax.plot(
        [table_left, table_left + table_width],
        [table_bottom, table_bottom],
        color="black",
        lw=0.8,
    )

    ax.plot(
        [table_left, table_left + benchmark_width],
        [table_top, header_bottom],
        color="black",
        lw=0.45,
    )
    ax.text(
        table_left + benchmark_width * 0.08,
        header_bottom + header_height * 0.18,
        "benchmark",
        ha="left",
        va="center",
        fontsize=10,
        fontfamily="serif",
    )
    ax.text(
        table_left + benchmark_width * 0.8,
        table_top - header_height * 0.2,
        "system",
        ha="center",
        va="center",
        fontsize=10,
        fontfamily="serif",
    )

    for col, host in enumerate(hosts):
        x = table_left + benchmark_width + col * cell_width
        ax.text(
            x + cell_width / 2,
            header_bottom + header_height * 0.32,
            host.capitalize(),
            ha="center",
            va="center",
            fontsize=10,
            fontfamily="serif",
        )

    previous_benchmark = None
    row_top = header_bottom
    for row, row_info in enumerate(row_infos):
        benchmark = row_info["benchmark"]
        config = row_info["config"]
        config_lines = row_info["config_lines"]
        row_height = row_heights[row]
        y = row_top - row_height
        if previous_benchmark is not None and benchmark != previous_benchmark:
            ax.plot(
                [table_left, table_left + table_width],
                [row_top, row_top],
                color="black",
                lw=0.25,
                alpha=0.4,
            )
        previous_benchmark = benchmark

        ax.text(
            table_left + 0.1,
            y + row_height * (0.68 if config_lines else 0.5),
            benchmark,
            ha="left",
            va="center",
            fontsize=9.5,
            fontfamily="serif",
        )
        for line_idx, config_line in enumerate(config_lines):
            ax.text(
                table_left + 0.24,
                y + row_height * 0.43 - line_idx * 0.13,
                config_line,
                ha="left",
                va="center",
                fontsize=6.8,
                fontfamily="serif",
                color="#444444",
            )

        for col, host in enumerate(hosts):
            x = table_left + benchmark_width + col * cell_width
            key = (benchmark, config)
            cell = matrix.get(key, {}).get(
                host, {"status": "Not Tested", "markers": []}
            )
            add_cell(ax, x, y, cell_width, row_height, cell["status"], cell["markers"])
        row_top = y

    draw_legend(ax, left, table_bottom - 0.2, content_width)

    fig.savefig(output_path, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def draw_legend(ax, left, top, table_width):
    ax.text(
        left,
        top - 0.05,
        "Status legend",
        ha="left",
        va="top",
        fontsize=10,
        fontweight="bold",
        fontfamily="serif",
    )
    ax.text(
        left + table_width * 0.62,
        top - 0.05,
        "Change legend",
        ha="left",
        va="top",
        fontsize=10,
        fontweight="bold",
        fontfamily="serif",
    )

    status_items = ["Not Tested", "Build", "Run", "Unknown", "Perf", "Pass"]
    row_height = 0.36
    swatch_width = 1.1
    swatch_height = 0.26
    start_y = top - 0.55

    for idx, status in enumerate(status_items):
        y = start_y - idx * row_height
        add_cell(ax, left, y, swatch_width, swatch_height, status)
        ax.text(
            left + swatch_width + 0.25,
            y + swatch_height / 2,
            STATUS_STYLES[status]["label"],
            ha="left",
            va="center",
            fontsize=10,
            fontfamily="serif",
        )

    change_x = left + table_width * 0.62
    change_items = [
        ("!", "Status changed"),
        ("dep", "Package changed"),
        ("sys", "System spec changed"),
        ("exp", "Experiment spec changed"),
        ("app", "Application spec changed"),
    ]
    for idx, (marker, label) in enumerate(change_items):
        y = start_y - idx * row_height
        ax.text(
            change_x,
            y + swatch_height / 2,
            marker,
            ha="left",
            va="center",
            fontsize=10,
            fontfamily="serif",
            fontweight="bold" if marker == "!" else "normal",
        )
        ax.text(
            change_x + 0.45,
            y + swatch_height / 2,
            label,
            ha="left",
            va="center",
            fontsize=10,
            fontfamily="serif",
        )


def main():
    args = parse_args()
    summary_path = Path(args.summary_json)
    output_path = summary_path.with_name("test_status_table.png")
    render_table(load_summary(summary_path), output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
