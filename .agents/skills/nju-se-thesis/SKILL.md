---
name: nju-se-thesis
description: 协助工程论文作者分析代码、写作、绘图、转换飞书材料和交付南京大学软件学院专业硕士论文。
metadata:
  version: "0.5.0"
  primary-language: "zh-CN"
  template: "nju-lug/NJUThesis@v1.5.1"
  optional-skills: ["archify", "lark-doc", "lark-whiteboard"]
  optional-bins: ["lark-cli", "njucli", "latexmk", "xelatex", "biber", "node", "docling"]
---

# 工程论文工具集

飞书是内容源稿。写作、代码说明、图表修改与文风校准都在飞书阶段完成；对话用于讨论和预览。TeX 只接收转换结果，负责排版、样式调整和编译。先确认输入目录和已有修改。

## 写作任务

先读用户指定的参考文档和本次写作材料。若未另指定参考，检查当前工作目录的 `references/local/index.md`，按页码读取相关原文与图表。索引缺失时直接使用用户给的文件，不依赖特定目录。

参考用于判断章节组织、论证和图文关系。记录具体依据及缺陷，不搬用段落、独有图示、数据或项目事实。他人论文不能代表用户个人文风；学校格式以当年要求为准。

结合作者自己的材料完成指定范围。章节写作读取 [角色分工](agents/agent.yaml)，使用与本次任务有关的职责；其中 Gemini Argon 是正文写作者偏好，实际调用入口与模型 ID 确认并调用成功后才算接通。角色指令本身不提供跨模型调度。下面的写作说明按需查阅，不作为每次写作的前置步骤。

| 任务 | 任务指令 |
|---|---|
| 材料梳理、题目与提纲 | [材料与提纲](references/writing-plan.md) |
| 知网检索、文献精读、相关工作 | [文献与相关工作](references/writing-literature.md) |
| 起草、续写与修改章节 | [章节写作](references/writing-chapters.md) |
| 分析仓库、代码摘录、工程图与数据图 | [代码与工程图表](references/writing-engineering.md) |
| 全文审查、一致性修订、交付核对 | [全文修订](references/writing-review.md) |
| 按样文校准文风、写原文评论与标记 | 调用工具集配套的 `$thesis-calibrate` Skill |

调用示例见 [写作指南](references/nju-se-engineering.md)，通用写作说明的方法出处见 [来源说明](references/writing-sources.md)。

## 共用规则

1. 以用户给定任务与材料为范围，已有目录和正文合理时直接沿用，只问影响本次结果的缺项。
2. 有材料的部分继续完成，缺失的实验、文献和实现不补造；建议与已完成事实分别表达。
3. reviewer 只返回评审建议，保持正文与文件原样；正文起草和修订由 writer 或作者完成。指令按列表组织，论文正文按论证关系成段。
4. 保留作者修订、原始文献键、图源与材料定位。写入后回读，未读全文不宣称完成全文审查。
5. 示例均为合成材料，只演示操作或写法，不作为作者项目事实。资料缺口和制作备注放在正文之外。

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

CLI 用法见工具仓库 README，各命令可用 `--help` 查看参数。

文献与 PDF 扩展见 [接入说明](references/integrations.md)：`literature-search` 检索与展开引用关系，`reference-check` 核对 DOI，`bibliography` 保留 Zotero 导出的引用键，`read-paper` 用 Docling 保存原页证据。`build` 默认执行 PDF.js 逐页对照；跳过预览必须记录，不能声称页面验收完成。

`plot` 与 `excerpt` 为飞书内容阶段准备图件和源码，其 TeX 片段只是排版产物。编译中发现事实、措辞、引文或图示错误时回到飞书修改，再导出；不在生成的 TeX 中另养一份正文。

## 论文检查

保留作者模板，学院当年要求优先。不能只因模板名是 NJUThesis 就认定已配置专业硕士；核对文档类型、学位类型、作者信息、字体和附录。只在标准样例中自动组稿，未知正文由代理核对后编辑。

转换报告中的缺项要定位原文处理。静态检查不展开任意 TeX 宏，PDF 结构检查不代替逐页审阅。编译禁用 shell escape 仍不是操作系统沙箱，只编译可信源。

安装 TeX 前读取 [TeX 环境](references/tex-macos.md) 并确认安装范围。工具依赖见 [依赖清单](references/dependencies.md)。用户提供 PDF 并明确要求送审自检时，可使用已安装的外部 `dongshao/nju-se-thesis-self-check`，结果不替代盲审。
