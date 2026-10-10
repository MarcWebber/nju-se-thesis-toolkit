# 图例

## 数据图

安装 `.[plots]` 后，可以直接从 CSV 生成配套的图源、SVG 和矢量 PDF：

```bash
thesis plot examples/figures/benchmark/data.csv /path/to/line --kind line --x concurrency --y baseline_p95_ms candidate_p95_ms --xlabel 并发请求数 --ylabel 'P95 延迟 / ms'
python /path/to/line/source/render.py /path/to/rebuilt
```

`plots.json` 给出折线、柱状、散点、箱线和直方图参数。箱线与直方图示例仅展示工具用法；正式实验应输入同一采样条件下的原始样本，不能把不同并发量的 P95 汇总值当作重复测量。

## 结构图

`document-flow.json` 是 Archify 架构图源，配套 `document-flow.svg` 为静态浅色矢量图。它说明论文材料处理关系，不代表所有环节均已自动接通。JSON 已通过结构检查，印刷尺寸和查看器视觉验收尚未完成。

在已安装的 Archify 目录执行，路径替换为本仓库绝对路径：

```bash
node bin/archify.mjs validate architecture /path/to/examples/figures/document-flow.json --quality showcase --json
node bin/archify.mjs deliver architecture /path/to/examples/figures/document-flow.json /path/to/diagram.html --quality showcase --json
```

从查看器导出浅色 SVG，保留 JSON。打印前检查实际栏宽下的文字大小和线条，不将 HTML 的结构校验当作论文印刷验收。

`benchmark/` 也保留独立可编辑的绘图脚本。自定义绘图时可执行：

```bash
python -m pip install -e '.[plots]'
python examples/figures/benchmark/plot.py /path/to/plot
thesis figure /path/to/figure-package --source examples/figures/benchmark --svg /path/to/plot/latency.svg --pdf /path/to/plot/latency.pdf --caption 演示数据排版 --label fig:latency --provenance 合成示例数据
```

脚本输出 SVG、矢量 PDF 和检查用 PNG。SVG 保留文字，PDF 嵌入字体；颜色之外同时使用线型和标记区分系列。数据没有实验含义，不可作为论文结论。
