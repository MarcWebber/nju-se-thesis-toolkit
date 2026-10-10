"""Rebuild a print-sized vector plot from synthetic demonstration data."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description="生成演示数据折线图")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if any((args.output / ("latency." + ext)).exists() for ext in ("svg", "pdf", "png")):
        parser.error("目标图已存在，请使用新目录")
    with Path(__file__).with_name("data.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    plt.rcParams.update({"font.size": 9, "svg.fonttype": "none", "pdf.fonttype": 42})
    fig, ax = plt.subplots(figsize=(5.5, 3.1), layout="constrained")
    for column, label, marker, line in (
        ("baseline_p95_ms", "Baseline", "o", "-"),
        ("candidate_p95_ms", "Candidate", "s", "--"),
    ):
        ax.plot([int(row["concurrency"]) for row in rows],
                [float(row[column]) for row in rows], label=label,
                marker=marker, linestyle=line, linewidth=1.4, markersize=4)
    ax.set(xlabel="Concurrent requests", ylabel="P95 latency / ms", ylim=(0, 135))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="0.88", linewidth=0.6)
    ax.legend(frameon=False)
    fig.suptitle("Synthetic data · layout example", fontsize=9)
    for extension in ("svg", "pdf", "png"):
        fig.savefig(args.output / ("latency." + extension), dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
