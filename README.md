# 工程论文工具集

面向工程论文作者的 Skill + CLI，由 AI 协助写作、分析代码、绘图和处理排版。飞书是内容源稿；TeX 是转换后的排版工程。

[使用状态](docs/status.md)汇总当前能力、本机入口、分发包和待验收项，并提供首个章节任务的调用示例。

[工具集成调研（2026-10-08）](docs/integration-survey-20261008.md)核对最新上游能力，比较文献检索、引用管理、PDF 解析与预览检查的接入价值。

**0.5.0 已接入第一批能力，共 19 个命令。** [真实接入验收](docs/delivery-check-20261008.md)包含本机 Zotero 自动导出和整篇编译结果。 [文献与 PDF 工具](docs/integrations.md)说明安装、OpenAlex 检索、Crossref 核对、Zotero 导出、Docling 原文解析，以及编译后的中文预览检查。

| 阶段 | 工具与职责 |
|---|---|
| 飞书内容 | 写作、代码说明、引用修订、原生画板、文风评论、本地重复比对 |
| 转换排版 | 飞书导出转 TeX、模板与样式调整、编译、引用和 PDF 检查 |
| 交付 | 飞书源稿、PDF、排版工程、可编辑图源、SVG 与矢量 PDF |

所有内容与图示修改先在飞书完成。编译后发现内容问题也回到飞书修改，再导出；不要求作者编辑 TeX。

## 写作入口

作者提供参考论文、自己的材料和目标章节，由 AI 直接读取原文后写作或审阅。[本地参考](references/README.md)记录文件位置、可借鉴页码和已知缺陷，后续可以替换。参考不是事实来源，不能换词抄段落或搬用图表与数据。

主要入口是 [nju-se-thesis](.agents/skills/nju-se-thesis/SKILL.md) 和 [文风校准](.agents/skills/thesis-calibrate/SKILL.md)。五份通用写作说明保留为按需参考；文件转换、绘图和编译仍可单独调用。纯写作不需要 Python 或 TeX。

[agent.yaml](.agents/skills/nju-se-thesis/agents/agent.yaml) 定义材料分析、正文写作和事实审阅三个职责。reviewer 只给评审建议，writer 或作者负责正文修改。reviewer 当前由本助手承担，MiniMax M3 列为待实测候选；正文写作者偏好 Gemini Argon，实际模型入口待确认。这是供 Skill 读取的角色指令，外部模型调用尚未接通。[试用稿审阅与改写](docs/writing-review-20261010.md)说明现有稿件的问题，并给出依据实际实现改写的一段正文。

```text
参照本地参考索引中的论文原页，根据我给的飞书方案和仓库，
只写“并发预约处理”一节，保留原术语和引用。
附一张飞书时序图，交付图源、SVG 和矢量 PDF。
没有性能数据，不写性能提升；不要修改业务代码。
```

写作顺序和人工介入见 [写作指南](.agents/skills/nju-se-thesis/references/nju-se-engineering.md)，开源能力与许可证核对见 [调研](.agents/skills/nju-se-thesis/references/writing-sources.md)。作者可以修改任意章节或图源，再单独执行相关任务。

知网检索由主 Skill 按[文献说明](.agents/skills/nju-se-thesis/references/writing-literature.md#知网)执行，复用浏览器登录态。本机账号保存在工作目录的 `.cnki.local.json`，字段为 `phone`；默认发布包不包含它。候选论文见[南大硕士参考](references/nju-masters-2025-2026.md)。

## 工具

每个命令直接处理指定输入，输出 JSON 和实际文件。

| 命令 | 用途 |
|---|---|
| `compare` | 本地比对稿件与指定参考资料，返回相似句段及来源 |
| `import-doc` | 飞书 XML 或导出 JSON 转 TeX |
| `table` | CSV 转三线表、跨页表和横向表 |
| `plot` | CSV 生成折线、柱状、散点、箱线和直方图 |
| `figure` | 图源、SVG、矢量 PDF 和插图片段打包 |
| `excerpt` | 摘录代码，记录文件、行号、版本与哈希 |
| `import-template` | 导入 NJUThesis 源 ZIP，保留备份 |
| `inspect-template` | 查看模板类型、版本和文件依赖 |
| `assemble` | 将章节填入已适配的 NJUThesis 示例副本 |
| `check` | 检查 TeX 文献键、标签、引用与缺失文件 |
| `build` | 在源工程副本中编译指定 TeX 主文件 |
| `check-log` | 检查编译错误、缺字与未解析引用 |
| `inspect-pdf` | 检查结构与中文字体映射，按需运行 PDF.js 对照或生成修复副本 |
| `literature-search` | OpenAlex 检索与引用关系展开 |
| `reference-check` | Crossref 核对 DOI 与 BibTeX 书目信息 |
| `bibliography` | 读取本地或 Zotero 导出，保留引用键并生成映射 |
| `read-paper` | Docling 解析 PDF、扫描件与文档，保留原页定位 |
| `pack` | 归档指定文件与目录，附 SHA-256 清单 |
| `doctor` | 查看命令与绘图依赖是否可用 |

写作和代码分析由代理按 [Skill](.agents/skills/nju-se-thesis/SKILL.md) 完成。结构图复用 Archify，在线文档复用 Lark CLI，学校平台复用 NjuCLI。

## 安装

Python 3.9 及以上。在仓库根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[plots]'
thesis doctor
```

不需要数据绘图时安装 `.` 即可。Matplotlib 是可选依赖，本地编译另需 TeX 工具、模板宏包与字体。

本机已配置 TeX Live 2026，中文编译与版本对照见 [本地 TeX 环境](docs/local-tex.md)。0.5.0 的 `build` 默认执行 PDF.js 检查；PDF.js、文献解析可选依赖和 Docling 独立环境见[安装说明](docs/integrations.md#安装)。

将仓库的 `.agents/skills/nju-se-thesis` 目录放到使用项目的 `.agents/skills/` 下，代理即可发现 Skill。wheel 同时携带 Skill、参考资料和样例，安装后位于 Python 环境的 `share/nju-se-thesis/`。

文风校准另安装同仓库的 `.agents/skills/thesis-calibrate`，可与主 Skill 一起复制。wheel 中位于 `share/nju-se-thesis/thesis-calibrate/`。

## 文风与重复检查

在 AI 助手中调用 [校准指令](.agents/skills/thesis-calibrate/SKILL.md)：

```text
$thesis-calibrate 飞书稿件链接
参照：references/local/index.md，或我指定的 PDF、个人样文
范围：系统实现章
在原文写局部评论与标记，不修改正文。
```

助手负责判断与建议，使用 Lark CLI 写评论并回读。接口支持按 block ID 定位，实际标记效果须写入后核对。本机快捷命令与底层 API 命令都因缺少评论 scope 停在授权检查；评论写回与页面标记尚未验收，正文读写已验证可用。他人论文只作文体参考，个人文风需提供自己的样文。

重复检查安装可选依赖 `pip install -e '.[similarity]'`，运行：

```bash
thesis compare ./draft.json ./reference.xml ./reference.txt --output ./comparison.json
```

输入支持飞书 fetch JSON、XML 和 UTF-8 TXT/MD，可比对整篇或选定章节。结果仅覆盖实际输入。输出保留原句、参考句、block ID 或行号、资料哈希；每句最多返回三条达到阈值的结果。默认最短 20 字符、相似度阈值 85，可用 `--min-chars` 和 `--threshold` 调整。

算法复用 [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz)，全程本地执行。阈值是筛选参数，不是准确率。它只覆盖给定资料的字面相似句段，不检索全网或论文库，不判断抄袭，不输出全文重复率或 AI 率。命中后须人工检查引文和常见技术表述；AI 检测模型尚未接入。

## 数据图与矢量交付

```bash
thesis plot examples/figures/benchmark/data.csv /path/to/latency \
  --kind line --x concurrency --y baseline_p95_ms candidate_p95_ms \
  --xlabel 并发请求数 --ylabel 'P95 延迟 / ms' \
  --caption 延迟对比 --label fig:latency

python /path/to/latency/source/render.py /path/to/rebuilt
```

`--kind` 支持 `line`、`bar`、`scatter`、`box`、`hist`。CSV 首行是列名。折线、柱状和散点默认第一列为横轴，其余列为数值系列；箱线和直方图用 `--y` 选择数值列。中文图自动选择覆盖文字的已安装字体，也可用 `--font` 指定字体族。

每张图交付：
`source/render.py`、`source/data.csv`、`source/plot.json`、依赖版本、`figure.svg`、`figure.pdf`、`figure.tex` 和清单。图源可在只有 Matplotlib 的环境重跑。

已有图件使用：

```bash
thesis figure /path/to/package --source /path/to/drawing-source \
  --svg /path/to/drawing.svg --pdf /path/to/drawing.pdf \
  --caption 系统架构 --label fig:architecture
```

图包同时要求源文件、SVG 和 PDF，拒绝 SVG 图片容器及含栅格图片的图件 PDF。结构检查不能证明图文一致或版式正确，仍需重绘和视觉检查。结构图方法与样例见 [图表说明](.agents/skills/nju-se-thesis/references/diagrams.md) 和 [图例](examples/figures/README.md)。

## 文档、表格与代码

```bash
thesis import-doc /path/to/lark-export.json /path/to/document \
  --assets /path/to/assets.json --source-url '原文链接'
thesis table /path/to/metrics.csv /path/to/table --caption 指标对比 --label tab:metrics
thesis table /path/to/wide.csv /path/to/wide-table --landscape
thesis excerpt /path/to/repo src/service.py /path/to/excerpt \
  --start 20 --end 45 --revision COMMIT --caption 请求处理 --label lst:request
```

文档命令接受 Lark CLI 完整 XML 或 fetch JSON，附件通过本地映射接入，保留原始输入和块 ID。支持基础标题、段落、列表、公式、代码、图片、分栏和普通表格。缺少附件、未映射引用、合并单元格及未知元素会写入报告，退出码为 2。见 [转换样例](examples/document-import/README.md)。

表格采用 `longtable` 与 `booktabs`，支持重复表头，横页另用 `pdflscape`。CSV 只包含值，不能恢复飞书公式、样式或合并关系。输出的 `preamble.tex` 列出需要的宏包。

代码摘录保留原始字节与来源，生成 `listings` 片段；省略版本则读取当前工作树。命令不执行仓库代码。机制分析方法见 [代码材料](.agents/skills/nju-se-thesis/references/code-evidence.md)。

## 模板与编译

```bash
thesis import-template /path/to/template.zip /path/to/paper --main njuthesis-sample.tex
thesis inspect-template /path/to/paper
thesis assemble /path/to/paper
thesis check /path/to/paper/build/project/njuthesis-sample.tex
thesis build /path/to/paper/build/project/njuthesis-sample.tex /path/to/compiled
```

导入保留原工程与源 ZIP。只有模板组稿使用 `thesis.json`、`outline.json` 和 `frontmatter.json`，格式见 [模板组稿](.agents/skills/nju-se-thesis/references/template.md)。自动填充只支持已核对的 NJUThesis v1.5.1 标准样例，未知正文不改写。

已有完整 TeX 工程可直接 `check` 和 `build`，无需导入模板。编译调用 XeLaTeX 与 latexmk，禁用 shell escape 和 latexmk 配置脚本，输出源副本、PDF 和完整日志。它不是操作系统沙箱，只编译可信工程。

编译超时默认 180 秒，可用 `--timeout` 指定正整数秒数。

转换、绘图、检查和本地编译不依赖 NJU TeX 账号。NJUThesis 是目前已适配的组稿模板，NJU TeX 是可选的在线服务。与线上对齐的是编译器、宏包和字体，不把平台地址或登录态写入通用工具。

在线登录、读写、上传、编译使用 [NjuCLI](.agents/skills/nju-se-thesis/references/nju-platform.md)。写入前确认具体目标，保留用户模板。

## 检查与归档

```bash
thesis check /path/to/main.tex --bib /path/to/references.bib
thesis check-log /path/to/main.log
thesis inspect-pdf /path/to/paper.pdf
thesis pack /path/to/delivery.zip /path/to/paper.pdf /path/to/tex-project /path/to/figures
```

引用检查沿静态 `input` 与 `include` 读取文件，不展开宏和条件分支。目录模式会合并扫描多个文档，优先传主文件。检查不会判断文献真实性、研究结论或学院格式。

`pack` 只收录明确指定的输入，不自动搜集其他材料，不覆盖已有 ZIP。交付时同时提供可编译源工程、原始图源、SVG 和矢量 PDF。图片数量为零不能代替实际视觉检查。

`inspect-pdf` 会检查中文 CID 字体的外部 CMap 依赖；加 `--preview-dir` 可运行 PDF.js 对照并保存逐页 PNG。`build` 默认执行全页对照；需要 Adobe GB1 修复时提供 `--cmap`，原编译 PDF 保留。仅编译可显式 `--skip-preview`，该结果不作为页面验收。完整参数见[中文 PDF 检查](docs/integrations.md#中文-pdf-检查)。

命令完成返回 0，检查发现问题返回 2，执行错误返回 1。语法、命令加载和实际运行记录见 [验证记录](docs/validation.md)。仓库变更按 [项目约定](AGENTS.md) 同步到配置的飞书文档。
