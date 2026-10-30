# 工程论文工具集 (`nju-se-thesis-toolkit`)

帮助南京大学软件学院专业硕士把项目代码、设计文档和实验记录整理成学位论文的 AI 技能与命令行工具集。

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB)](pyproject.toml) [![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[核心功能](#核心功能) · [快速开始](#快速开始) · [使用示例](#使用示例) · [文档](#文档) · [贡献](#贡献) · [许可证](#许可证)

## 核心功能

- **论文起草与代码梳理**：结合真实工程代码、设计说明和实验记录起草章节，在飞书文档中维护正文、图表与引用修改。
- **参考审阅与文风校准**：对照指定参考论文或作者本人样文逐段审阅；审稿角色（reviewer）只给修改建议，由写作者或作者本人修改正文。
- **文献检索与元数据核对**：通过 OpenAlex 检索相关论文，使用 Crossref 核对 DOI 与 BibTeX 书目信息，调用 Docling 解析 PDF 原页。
- **图表生成与飞书转换**：将 CSV 实验数据绘制成统计图或三线表，将飞书导出的文档转换为 TeX 正文片段。
- **模板编译与中文 PDF 检查**：基于 `NJUThesis v1.5.1` 标准样例组稿编译，默认运行 PDF.js 全页检查并排查中文字体映射与缺字问题。
- **协作问题排查**：AI 协作中出现理解偏差、范围膨胀、角色越界、版本混乱、图示或验收问题时，助手按症状定位原因，在已有授权内修复，并分别说明已经核验的事实和需要读者评价的效果。这个 Skill 可以独立使用，同样适用于其他项目。

## 快速开始

本仓库为公开仓库（源码版本 `0.5.0`），可直接从源码克隆安装。工具集由两部分组成：`Skills` 是给 AI 助手读取的任务说明，配套 `CLI` 是实际执行文件转换、绘图和编译的本地命令行程序（非 MCP 服务）。

### 1. 复制 Skill 到你的论文工作区

如果目前只进行正文起草和文字讨论，只需克隆本仓库并将三个 Skill 目录复制到你的论文工作区（请将 `/path/to/thesis-project` 替换为你的实际目录）：

```bash
git clone https://github.com/MarcWebber/nju-se-thesis-toolkit.git
cd nju-se-thesis-toolkit
mkdir -p /path/to/thesis-project/.agents/skills
cp -R .agents/skills/nju-se-thesis .agents/skills/thesis-calibrate .agents/skills/collaboration-troubleshooting /path/to/thesis-project/.agents/skills/
```

`collaboration-troubleshooting` 处理通用的 AI 协作问题，可以脱离论文 Skill 和 CLI 独立使用。在其他项目中使用时，你只需单独复制这个目录：

```bash
mkdir -p /path/to/project/.agents/skills
cp -R .agents/skills/collaboration-troubleshooting /path/to/project/.agents/skills/
```

支持 `.agents/skills/` 目录约定的 AI 助手加载工作区后，可通过 `$nju-se-thesis`、`$thesis-calibrate` 或 `$collaboration-troubleshooting` 显式调用，也可由宿主环境按任务描述自动选择（是否支持自动选择取决于宿主客户端，AI 仅读取本 README 并不能自动获得调用能力）。纯文字讨论可直接开始；若需助手直接读写你的飞书文档，还需在本地配置并授权 `lark-cli`（飞书局部评论写回目前待权限验收）。

### 2. 安装命令行工具（CLI）

当需要执行文献检索、数据绘图、飞书转 TeX 或编译检查时，在克隆下来的工具集仓库根目录创建虚拟环境并安装（要求 Python 3.9+）：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[plots]'
.venv/bin/thesis doctor
```

无需数据绘图可安装 `.`；需要本地相似句段比对请安装 `.[similarity]`，需要读取 BibTeX 请安装 `.[references]`。直接调用 `.venv/bin/thesis`（或其绝对路径）即可执行命令，无需依赖后续终端保持虚拟环境激活状态。上述 `pip` 命令不会自动安装 TeX、字体、PDF.js 或 Docling，请根据 `.venv/bin/thesis doctor` 的提示，对照 [文献与 PDF 工具](docs/integrations.md#安装) 和 [TeX 安装](.agents/skills/nju-se-thesis/references/tex-macos.md) 单独安装。

## 使用示例

### 对话任务示例

在加载了 Skill 的助手中，可以直接用自然语言发起写作、核对或检查任务：

```text
$nju-se-thesis
源稿：我的飞书文档链接
材料：相关代码仓库路径、设计说明、实验记录
参考：指定参考论文 PDF 或我自己的样文
范围：系统实现章的“并发预约处理”一节
请根据实际代码和设计材料，写清并发预约的处理流程与设计理由，保留原有专业术语和文献引用；需要配图时补一张时序图。如果现有材料里有缺口，请单独列出来。
```

也可以直接要求助手调用 CLI 完成专项核查，例如：

- `核对 DOI 10.1038/nature14539 并保存书目信息`
- `检查这份 PDF 是否有中文缺字`

日常修改正文、代码说明和图表均在飞书中完成，定稿后导出到 TeX 仅做排版和编译；若在 PDF 中发现事实、措辞或图示错误，请退回飞书修改源稿再重新导出，不必同时维护两份正文。写作所需的项目事实与实验数据需由作者提供；参考论文可用于支撑研究背景、理论与相关工作，以及参考章节组织和论证方式，但不能冒充作者自己的实验与工程事实；校准个人文风需使用作者自己的样文。

### 协作问题排查示例

当助手的结果偏离要求，或交付过程中出现角色、版本、验收方面的问题时，你可以把现象直接交给排查 Skill：

```text
$collaboration-troubleshooting
现象：我只要求补一张时序图，结果多了三份说明文档，原有小节也被改写了。
期望：找出偏差原因，恢复我认可的内容，只保留这张时序图，并告诉我怎样确认已经改好。
```

助手会依据你的原话和现有文件定位偏差，在你已经授权的范围内修复，保留你认可的内容，并分别说明已经核验的事实和需要你阅读后评价的效果。

### 命令行常用操作

| 要做什么 | 怎么做 |
| :--- | :--- |
| 检索相关文献 | 用 `literature-search` 搜索相关论文并获取基本文献信息。 |
| 生成实验图表 | 用 `plot` 把 CSV 实验数据画成论文所需的统计图。 |
| 转换飞书稿件 | 用 `import-doc` 把飞书导出的内容转成 TeX 正文片段。 |
| 编译与检查排版 | 用 `build` 在工程副本中编译主文件并默认运行 PDF.js 全页检查。 |
| 比对相似段落 | 用 `compare` 排查草稿与指定参考资料中字面相似的句子。 |

模板组稿主要适配 `NJUThesis v1.5.1` 标准样例，正式提交前请以学院当年的格式要求为准；其余子命令可通过 `.venv/bin/thesis --help` 查看。

以下示例请将 `/path/to/...` 替换为实际路径；文献检索、DOI 核对与 PDF 解析等命令的输出目录须为新的空目录：

```bash
# 检索相关文献并输出到新的空目录
.venv/bin/thesis literature-search 'document parsing' --limit 5 --output output/papers

# 在工程副本中编译主文件（默认运行 PDF.js 全页检查）
.venv/bin/thesis build /path/to/main.tex /path/to/compiled
```

文献题录核对不能代替阅读原文确认论断，扫描件 OCR 解析结果建议回原页核对；`compare` 仅比对所传入的指定资料。自动检查不能代替逐页审阅最终 PDF 页面；编译虽禁用了 shell escape，但并非操作系统沙箱，请只编译来源可信的 TeX 工程。

## 文档

- **Skill 说明**：[论文写作 Skill](.agents/skills/nju-se-thesis/SKILL.md) · [文风校准 Skill](.agents/skills/thesis-calibrate/SKILL.md) · [协作问题排查 Skill](.agents/skills/collaboration-troubleshooting/SKILL.md)
- **写作与图表**：[写作指南](.agents/skills/nju-se-thesis/references/nju-se-engineering.md) · [参考阅读说明](references/README.md) · [图表说明](.agents/skills/nju-se-thesis/references/diagrams.md)
- **模板与环境**：[模板组稿](.agents/skills/nju-se-thesis/references/template.md) · [TeX 安装](.agents/skills/nju-se-thesis/references/tex-macos.md) · [文献与 PDF 工具](docs/integrations.md)
- **进展与记录**：[使用状态](docs/status.md) · [验证记录](docs/validation.md) · [通用协作复盘](docs/collaboration-lessons.md)

## 贡献

发现问题或提交改进请直接在仓库的 [Issues](https://github.com/MarcWebber/nju-se-thesis-toolkit/issues) 或 [Pull Requests](https://github.com/MarcWebber/nju-se-thesis-toolkit/pulls) 中提出。

## 许可证

本项目采用 [MIT 许可证](LICENSE)。
