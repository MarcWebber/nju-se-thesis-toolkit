# 工程论文工具集 (`nju-se-thesis-toolkit`)

这套工具帮助南京大学软件学院专业硕士把手里已有的项目代码、设计文档和实验记录整理成学位论文。你可以让 AI 助手对照真实工程材料起草章节、梳理实现逻辑、润色文风，再用配套的命令行工具完成图表绘制、文献整理和 LaTeX 排版编译。

## 开始写一个章节

把仓库里的两个 Skill 目录复制到你论文项目的 `.agents/skills/` 下，支持该目录约定的 AI 助手就能直接读取任务说明：

- [论文写作 Skill](.agents/skills/nju-se-thesis/SKILL.md)（`.agents/skills/nju-se-thesis/`）：结合代码、设计材料与实验记录协助起草正文、生成图表、转换飞书稿件和调用编译。
- [文风校准 Skill](.agents/skills/thesis-calibrate/SKILL.md)（`.agents/skills/thesis-calibrate/`）：对照参考论文或你的样文逐段审阅，指出重复、空泛或逻辑不顺的地方。审稿角色（reviewer）只给修改建议，由写作者或你本人修改正文；当前先在对话中返回评审建议，飞书局部评论写回待权限验收。

如果只是纯文字讨论和预览草稿，复制上述目录后就能开始，无需先装 Python 或 TeX；若要让助手直接读写你的飞书文档，还需在本地配置并授权 `lark-cli`。准备好后，可以这样向助手发起任务：

```text
$nju-se-thesis
源稿：我的飞书文档链接
材料：相关代码仓库路径、设计说明、实验记录
参考：指定参考论文 PDF 或我自己的样文
范围：系统实现章的“并发预约处理”一节

请根据实际代码和设计材料，写清并发预约的处理流程与设计理由，保留原有专业术语和文献引用；需要配图时补一张时序图。如果现有材料里有缺口，请单独列出来。
```

日常写作时，正文起草、代码说明、图表修改和引用标注都在飞书文档里完成。你可以在对话中与 AI 讨论思路、预览草稿，确认后再更新飞书；定稿后导出到 TeX 只做排版、样式调整和编译。如果看 PDF 时发现事实、措辞或图示有误，直接回飞书修改并重新导出，不必同时维护两份正文。

写作需要由你提供项目事实、实验数据和已有稿件，缺失的实验或实现细节需由你补充确认。参考论文可以用来支持研究背景、理论与相关工作，或参考章节组织、论证推进与图文配合方式，但不能代替你亲自做过的工程和实验；校准个人文风时，只有你自己的样文能作为个人习惯依据。

## 安装命令行工具

当你需要解析文献、绘制数据图表、把飞书稿件转进模板或编译 PDF 时，在下载后的仓库根目录下创建虚拟环境并安装命令行工具（要求 Python 3.9+）：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[plots]'
thesis doctor
```

不需要数据绘图时可只安装 `.`；需要本地相似句段比对请安装 `.[similarity]`，需要读取 BibTeX 请安装 `.[references]`。上述 `pip` 命令不会安装 TeX、字体、PDF.js 或 Docling，你可以运行 `thesis doctor` 检查外部依赖状态，按 [文献与 PDF 工具](docs/integrations.md#安装) 和 [TeX 安装](.agents/skills/nju-se-thesis/references/tex-macos.md) 单独配置。

## 常用操作

安装完成后，可通过 `thesis` 命令处理日常排版与核查任务，运行 `thesis --help` 可查看其余子命令：

| 要做什么 | 怎么做 |
| :--- | :--- |
| 检索相关文献 | 用 `literature-search` 搜索相关论文并获取基本文献信息。 |
| 生成实验图表 | 用 `plot` 把 CSV 实验数据画成论文所需的统计图。 |
| 转换飞书稿件 | 用 `import-doc` 把飞书导出的内容转成 TeX 正文片段。 |
| 编译与检查排版 | 用 `build` 在工程副本中编译主文件并默认运行 PDF.js 全页检查。 |
| 比对相似段落 | 用 `compare` 排查草稿与指定参考资料中字面相似的句子。 |

模板组稿主要适配 `NJUThesis v1.5.1` 标准样例，正式提交前请以学院当年的格式要求为准；其余子命令可通过 `thesis --help` 查看。

下面是检索文献与编译排版两个常用示例。请将 `/path/to/...` 替换为你的实际路径；文献检索、元数据核对与 PDF 解析等命令的输出目录须为新的空目录：

```bash
# 检索相关文献并输出到新目录
thesis literature-search 'document parsing' --limit 5 --output output/papers

# 在工程副本中编译主文件（默认运行 PDF.js 全页检查）
thesis build /path/to/main.tex /path/to/compiled
```

工具核对的文献元数据不能代替你阅读原文确认论断，扫描件解析结果也建议回原页核对。`build` 和 `inspect-pdf` 的自动检查不能代替逐页审阅最终 PDF 页面；编译虽禁用了 shell escape，但仍非操作系统沙箱，请只编译来源可信的 TeX 工程。

## 更多文档

- **写作与阅读**：[写作指南](.agents/skills/nju-se-thesis/references/nju-se-engineering.md) · [参考阅读说明](references/README.md)
- **图表与转换**：[图表说明](.agents/skills/nju-se-thesis/references/diagrams.md) · [图例](examples/figures/README.md) · [转换样例](examples/document-import/README.md)
- **模板与环境**：[模板组稿](.agents/skills/nju-se-thesis/references/template.md) · [TeX 安装](.agents/skills/nju-se-thesis/references/tex-macos.md) · [南大在线平台](.agents/skills/nju-se-thesis/references/nju-platform.md) · [文献与 PDF 工具](docs/integrations.md)
- **状态与记录**：[使用状态](docs/status.md) · [真实接入验收](docs/delivery-check-20261008.md) · [验证记录](docs/validation.md)
