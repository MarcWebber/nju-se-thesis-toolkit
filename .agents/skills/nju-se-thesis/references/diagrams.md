# 论文图表

## 图型

- `architecture`：系统组件、边界和部署关系。
- `workflow`：业务流程、工程流程和异常分支。
- `sequence`：接口调用、异步链路和返回关系。
- `dataflow`：数据来源、处理、存储和使用方。
- `lifecycle`：状态、事件、重试和终态。

UML 类图、ER 图和标准用例图优先使用专门建模工具。

| 图型 | 必须表达 | 排版重点 |
|---|---|---|
| 架构图 | 组件职责、边界、真实依赖 | 单一抽象层，关系标明协议或动作 |
| 流程图 | 主路径、决策条件、失败出口 | 优先纵排，避免一页塞入所有分支 |
| 时序图 | 参与者、调用顺序、异步与返回 | 横向按参与者展开，长链分场景 |
| 数据流图 | 来源、转换、存储、消费 | 区分数据流与控制调用 |
| 状态图 | 事件、条件、重试、终态 | 状态来自实际修改处，不推测转移 |
| 指标图 | 坐标、单位、口径、样本和对照 | 不截轴夸大差异，灰度下仍可区分 |

架构图的可运行 JSON 和指标图的脚本、CSV 见仓库 `examples/figures/`。架构、流程、时序等结构图复用 Archify，统计图使用 Matplotlib 的原生 SVG/PDF 导出，不另写渲染器。

## 导出

按 `$archify` 流程验证并交付 HTML，再检查实际渲染效果。从查看器导出浅色 SVG，使用现有矢量转换工具输出 PDF；转换后核对文字、箭头、字体和裁剪。不能用浏览器截图代替矢量导出。

论文插图使用浅色背景，检查中文字体、线宽、灰度辨识度和缩放后的字号。自动验证通过不等于完成视觉检查。

宽图先调整结构与分组，确需横页时由模板使用横向页；长流程拆成能独立解释的子图。并列图保持共同基线、各自题注和一致尺度。不要为塞进页面把文字缩到无法阅读。

## 图包

数据图可直接生成并交付：

```bash
thesis plot data.csv /path/to/latency --kind line --x concurrency --y baseline candidate --xlabel 并发请求数 --ylabel 延迟 --caption 延迟对比 --label fig:latency
python /path/to/latency/source/render.py /path/to/rebuilt
```

`line` 用于有顺序的趋势，`bar` 用于类别对比，`scatter` 用于成对数值关系，`box` 用于样本分布与离群点，`hist` 用于频数分布。箱线和直方图输入原始样本，不能把不同工况的汇总值当作同一实验的重复测量。保留坐标单位、采样条件和数据口径。

图源包含 CSV、实际参数、独立重绘脚本和依赖版本。重跑使用本机对应字体，检查 SVG 与 PDF，再按论文栏宽查看。

```bash
thesis figure /path/to/package --source /path/to/source --svg /path/to/figure.svg --pdf /path/to/figure.pdf --caption 请求链路 --label fig:request --provenance 源码位置或数据来源
```

交付包含 `source/`、`figure.svg`、`figure.pdf`、`figure.tex` 和哈希清单。图源目录应包含重建需要的代码、数据和说明，不包含账号凭据。TeX 片段默认引用同目录的 `figure.pdf`，移入子目录后由代理更新路径。

SVG 检查拒绝图片容器、脚本和外部资源，图件 PDF 检查拒绝栅格图片对象。它们不证明图元可见、源图与导出图一致或打印效果。交付前运行图源重建，并在论文实际尺寸下审阅。

## Visio

本工具集未提供 `.vsdx` 转换能力。需要 Visio 交付时，另行选择制作或转换工具，并检查文字可编辑性、连接线、箭头方向、字体和页面裁剪。
