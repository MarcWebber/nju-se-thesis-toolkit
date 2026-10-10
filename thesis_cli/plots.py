"""Create reproducible vector charts from CSV data."""

import inspect
import json
from pathlib import Path
import shutil
import tempfile


def _render(data, output, config):
    import csv
    import math
    from pathlib import Path

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib import font_manager
    from matplotlib.ft2font import FT2Font

    with Path(data).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        columns, rows = reader.fieldnames or [], list(reader)
    if not columns or len(set(columns)) != len(columns) or not rows:
        raise ValueError("CSV 需要唯一的列名和至少一行数据")
    kind = config["kind"]
    if kind not in {"line", "bar", "scatter", "box", "hist"}:
        raise ValueError("图型应为 line、bar、scatter、box 或 hist")
    x = config.get("x") or (columns[0] if kind in {"line", "bar", "scatter"} else None)
    names = config.get("y") or [name for name in columns if name != x]
    names = [names] if isinstance(names, str) else list(names)
    if not names or any(name not in columns for name in names) or x and x not in columns:
        raise ValueError("选择的绘图列不存在或没有数值列")

    def number(value, column):
        try:
            result = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("列 " + column + " 包含非数值：" + str(value)) from exc
        if not math.isfinite(result):
            raise ValueError("列 " + column + " 包含非有限数值")
        return result

    series = [[number(row.get(name), name) for row in rows
               if kind not in {"box", "hist"} or row.get(name) not in (None, "")]
              for name in names]
    if any(not values for values in series):
        raise ValueError("数值列不能为空")
    ticks = [row.get(x) for row in rows] if x else []
    if x and any(value in (None, "") for value in ticks):
        raise ValueError("横轴列不能为空")
    positions = ticks
    if kind == "scatter":
        positions = [number(value, x) for value in ticks]
    elif kind == "line":
        try:
            positions = [number(value, x) for value in ticks]
        except ValueError:
            positions = list(range(len(ticks)))

    xlabel = config.get("xlabel") or (x or "")
    ylabel = config.get("ylabel") or ("Count" if kind == "hist" else names[0] if len(names) == 1 else "")
    if kind == "hist" and not config.get("xlabel"):
        xlabel = names[0] if len(names) == 1 else "Value"
    text = "".join([config.get("title", ""), xlabel, ylabel, *names, *(ticks if kind in {"line", "bar"} else [])])
    characters = {ord(char) for char in text + "0123456789.−" if not char.isspace()}
    requested_font = config.get("font")
    candidates = [requested_font] if requested_font else ["DejaVu Sans", "Noto Sans CJK SC", "PingFang SC", "Heiti SC", "Heiti TC", "Arial Unicode MS", "Microsoft YaHei", "SimHei"]
    selected_font = None
    for name in candidates:
        try:
            path = font_manager.findfont(name, fallback_to_default=False)
            if characters <= set(FT2Font(path).get_charmap()):
                selected_font = name
                break
        except ValueError:
            continue
    if not selected_font:
        raise ValueError("找不到覆盖图中文字的字体，请用 --font 指定已安装字体")
    config.update(x=x, y=names, xlabel=xlabel, ylabel=ylabel,
                  font=selected_font, matplotlib=matplotlib.__version__)
    plt.rcParams.update({"font.family": selected_font, "font.size": 9,
                         "svg.fonttype": "none", "svg.hashsalt": "nju-se-thesis",
                         "pdf.fonttype": 42})
    output = Path(output)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("绘图输出目录必须不存在或为空")
    output.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.5, 3.2), layout="constrained")
    markers, styles, hatches = ["o", "s", "^", "D", "v", "P"], ["-", "--", "-.", ":"], ["", "/", "\\", "x", ".", "+"]
    try:
        if kind == "box":
            ax.boxplot(series)
            ax.set_xticks(range(1, len(names) + 1), names)
        else:
            bins = np.histogram_bin_edges([value for values in series for value in values], bins="auto") if kind == "hist" else None
            for index, (name, values) in enumerate(zip(names, series)):
                marker, style = markers[index % len(markers)], styles[index % len(styles)]
                if kind == "line":
                    ax.plot(positions, values, label=name, marker=marker, linestyle=style, linewidth=1.3, markersize=4)
                    if positions == list(range(len(ticks))):
                        ax.set_xticks(positions, ticks)
                elif kind == "bar":
                    width = 0.8 / len(names)
                    offset = (index - (len(names) - 1) / 2) * width
                    ax.bar([row + offset for row in range(len(ticks))], values, width,
                           label=name, hatch=hatches[index % len(hatches)], edgecolor="0.2", linewidth=0.5)
                    ax.set_xticks(range(len(ticks)), ticks)
                elif kind == "scatter":
                    ax.scatter(positions, values, label=name, marker=marker, s=22)
                elif kind == "hist":
                    ax.hist(values, bins=bins, label=name, histtype="step", linestyle=style, linewidth=1.4)
            if len(names) > 1:
                ax.legend(frameon=False)
        ax.set(title=config.get("title", ""), xlabel=xlabel, ylabel=ylabel)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="0.88", linewidth=0.6)
        ax.set_axisbelow(True)
        fig.savefig(output / "figure.svg", metadata={"Date": None})
        fig.savefig(output / "figure.pdf", metadata={"CreationDate": None, "ModDate": None})
    finally:
        plt.close(fig)


def create_plot(data, output, kind="line", x=None, y=None, title="", xlabel="", ylabel="",
                caption="", label="", font=None):
    """Build a figure package containing CSV, standalone renderer, SVG and PDF."""
    from .figures import package_figure

    data, output = Path(data), Path(output)
    if output.is_symlink() or output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("绘图交付目录必须不存在或为空，不覆盖已有内容")
    config = dict(kind=kind, x=x, y=y, title=title, xlabel=xlabel, ylabel=ylabel, font=font)
    with tempfile.TemporaryDirectory(prefix="thesis-plot-") as temporary:
        source, rendered = Path(temporary) / "source", Path(temporary) / "rendered"
        source.mkdir()
        shutil.copyfile(data, source / "data.csv")
        try:
            _render(source / "data.csv", rendered, config)
        except ImportError as exc:
            raise ValueError("数据绘图需要 Matplotlib，请安装 nju-se-thesis[plots]") from exc
        (source / "plot.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (source / "requirements.txt").write_text("matplotlib==" + config["matplotlib"] + "\n", encoding="utf-8")
        script = inspect.getsource(_render) + '''
if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="从已交付的 CSV 和配置重建矢量图")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    _render(source / "data.csv", args.output, json.loads((source / "plot.json").read_text(encoding="utf-8")))
'''
        (source / "render.py").write_text(script, encoding="utf-8")
        return package_figure(output, source, rendered / "figure.svg", rendered / "figure.pdf",
                              caption=caption, label=label, provenance="CSV: " + str(data.absolute()))
