---
name: nju-se-thesis
description: 用于南京大学软件学院专业硕士论文的工程论文写作、论文检索与 DOI 核对、图表制作、飞书转 TeX 及中文 PDF 检查。
metadata:
  version: "0.5.0"
  primary-language: "zh-CN"
  template: "nju-lug/NJUThesis@v1.5.1"
  optional-skills: ["archify", "lark-doc", "lark-whiteboard"]
  optional-bins: ["lark-cli", "njucli", "latexmk", "xelatex", "biber", "node", "docling"]
---

# 工程论文工具集

飞书文档是内容源稿。正文起草、代码说明、图表修改和文风校准都在飞书中完成；对话用于讨论方案和预览内容。TeX 只接收导出的转换结果，负责排版、样式调整与编译；事实和措辞问题退回飞书修订。动手前先确认输入目录和已有修改。

## 调用命令行

纯文字写作与讨论不强制检查命令行工具。当任务涉及文献检索、DOI 核对、PDF 解析、图表生成、飞书转换、模板编译或 PDF 检查时，按以下步骤调用 CLI：

1. **定位可执行文件**：依次检查环境变量 `PATH` 中的 `thesis`、当前工作区的 `.venv/bin/thesis` 或用户提供的已安装路径。由于终端环境常未激活虚拟环境（`command -v thesis` 可能为空），确认可执行文件存在后请记住其绝对路径，后续命令均用该绝对路径替换示例中的 `thesis` 前缀。
2. **确认版本与参数**：先运行 `<thesis路径> --version` 确认工具可用，再按本次任务读取对应子命令的 `--help`。`thesis doctor` 仅用于定位依赖项是否存在，不能证明飞书授权已打通或 TeX 工程可正常编译。
3. **缺失处理与跨项目定位**：若找不到 CLI，读取 [依赖与安装](references/dependencies.md)，向用户说明缺项并按实际安装条件处理；若已有可用环境，直接使用，不重复安装。将本 Skill 复制到其他项目目录使用时，先核对 PDF.js 与 Docling 等依赖能否正常定位，无法自动定位时再按依赖说明显式指定路径。
4. **真实执行与结果核对**：实际运行命令并读取生成的输出文件，不能仅向用户展示命令就声称任务已完成。根据退出码处理结果：`0` 表示执行完成，`2` 表示发现需处理的检查问题，`1` 表示执行失败。

## 写作任务

读取作者当前要求和指定材料，按 [写作指南](references/nju-se-engineering.md) 使用参考资料、确认范围并交接写作。指南链接领域方法，项目事实与个人偏好从当前工作区的本地资料按需读取。

作者指定外部写作者时，按 [角色分工](agents/agent.yaml) 提供目标、事实与出处，由写作者自主组织内容；评审者提交有依据的建议。模型和入口沿用作者本次选择。

| 任务 | 任务指令 |
|---|---|
| 材料梳理、题目与提纲 | [材料与提纲](references/writing-plan.md) |
| 知网检索、文献精读、相关工作 | [文献与相关工作](references/writing-literature.md) |
| 起草、续写与修改章节 | [章节写作](references/writing-chapters.md) |
| 分析仓库、代码摘录、工程图与数据图 | [代码与工程图表](references/writing-engineering.md) |
| 全文审查、一致性修订、交付核对 | [全文修订](references/writing-review.md) |
| 按样文校准文风、写原文评论与标记 | 调用工具集配套的 `$thesis-calibrate` Skill |
| 协作中出现理解偏差、范围膨胀、角色越界、版本混乱、图示或验收问题 | 调用工具集配套的 `$collaboration-troubleshooting` Skill，项目事实仍按写作指南从本地资料读取 |

写作说明的方法出处见 [来源说明](references/writing-sources.md)。

## 工具选择

### 飞书内容阶段

| 任务 | 操作 |
|---|---|
| 正文与引用 | 使用 `lark-doc` 在飞书稿件中修改 |
| 文风校准 | 调用 `$thesis-calibrate`，写入局部评论与标记 |
| 重复句段 | `thesis compare` 对指定参考资料做本地比对，结果回查原段落 |
| 代码分析与摘录 | 读取 [代码材料](references/code-evidence.md)，由代理分析，`thesis excerpt` 保存代码与来源，说明写回飞书 |
| 数据图 | 读取 [图表说明](references/diagrams.md)，`thesis plot` 生成图源、SVG 和 PDF，回到飞书展示与确认 |
| 结构图 | 使用 `lark-whiteboard` 原生画板；另按图表说明交付可编辑源、SVG 和矢量 PDF |

### 转换与排版阶段

| 任务 | 操作 |
|---|---|
| 文档转换 | 读取 [飞书材料](references/lark-source.md)，调用 `thesis import-doc` |
| 表格排版 | `thesis table` 将 CSV 转三线表与跨页表，宽表可用 `--landscape` |
| 图件转换与打包 | `thesis figure` 收录飞书阶段确认的图源、SVG 和矢量 PDF |
| 模板组稿 | 读取 [模板组稿](references/template.md)，导入源 ZIP 并填充模板副本 |
| 检查与编译 | 对实际主文件运行 `thesis check`、`thesis build`，对结果运行 `check-log`、`inspect-pdf` |
| 在线读写 | 读取 [南大平台](references/nju-platform.md)，使用已有 NjuCLI |
| 归档 | `thesis pack` 收录明确指定的论文、工程、图源与报告 |

CLI 用法见 [依赖与安装](references/dependencies.md)，各命令可用 `--help` 查看参数。

文献与 PDF 扩展见 [接入说明](references/integrations.md)：`literature-search` 检索与展开引用关系，`reference-check` 核对 DOI，`bibliography` 保留 Zotero 导出的引用键，`read-paper` 用 Docling 保存原页证据。`build` 默认执行 PDF.js 逐页对照；跳过预览必须记录，不能声称页面验收完成。

`plot` 与 `excerpt` 为飞书内容阶段准备图件和源码，其 TeX 片段只是排版产物。编译中发现事实、措辞、引文或图示错误时回到飞书修改，再导出；不在生成的 TeX 中另养一份正文。

## 论文检查

保留作者模板配置，格式要求以学院当年规定为准。不能仅凭模板名为 NJUThesis 就认定已配好专业硕士参数，需核对文档类型、学位类型、作者信息、字体和附录。只在标准样例中自动组稿，结构未知的正文先由代理核对再编辑。

转换报告中的缺项按提示定位回对应的原始材料处理（如飞书正文、导出图片素材或本地文件）；涉及事实与措辞错误时仍退回飞书修订。静态检查不展开任意 TeX 宏，PDF 结构检查不代替逐页审阅页面。编译时禁用 shell escape 仍不是操作系统沙箱，只编译可信源。

安装 TeX 前读取 [TeX 环境](references/tex-macos.md) 并确认安装范围。工具依赖见 [依赖清单](references/dependencies.md)。用户提供 PDF 并明确要求送审自检时，可使用已安装的外部 `dongshao/nju-se-thesis-self-check`，结果不替代盲审。
