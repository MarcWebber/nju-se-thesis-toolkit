# 工具能力与集成调研

后续实现：第一批能力已在 0.5.0 接入，当前共 19 个命令；用法与实际验证见[文献与 PDF 工具](integrations.md)。下文保留本次接入前的调研快照。

核对日期：2026-10-08。范围是本项目的论文工具集；全网检索用于发现候选，技术结论以官方文档、仓库和发布页为准。下列优先级是结合当前缺口作出的集成建议，上游支持的功能尚未自动成为本工具集的能力。

## 当前能力

本机 `thesis` 为 **0.4.0，两个 Skill、15 个命令**。主流程已覆盖飞书写作、代码证据、图表、TeX 转换、模板组稿、本地编译和归档。此前完整试用稿为 22 页；本次重新检查入口和依赖，没有重跑整篇编译。

| 范围 | 已有入口 | 数量 |
|---|---|---:|
| 材料转换与证据 | `import-doc`、`excerpt`、`table` | 3 |
| 图件 | `figure`、`plot` | 2 |
| 模板与组稿 | `import-template`、`inspect-template`、`assemble` | 3 |
| 检查 | `check`、`check-log`、`inspect-pdf` | 3 |
| 指定资料相似句比对 | `compare` | 1 |
| 编译、归档、环境 | `build`、`pack`、`doctor` | 3 |
| 合计 | 不含外部工具的子命令 | **15** |

两个 Skill 分别负责论文写作工作流和文风校准。Skill 是代理执行指引，其数量不能当作已经独立实现的软件功能数。

本机 Lark CLI 为 1.0.80；NjuCLI 为 0.1.0，已在 PATH，可直接调用 `njucli tex`。后者当前有 13 个业务子命令，涉及模板、项目、文件、编译、日志和 PDF，不计入上述 15 个命令。`doctor` 可以定位 latexmk、XeLaTeX、Biber 和两套 CLI。NjuCLI 帮助中未发现切换项目编译器的入口，不能据此关闭线上 XeLaTeX 编译待办。

当前主要缺口是文献发现、统一引用库和带原页定位的论文解析。`inspect-pdf` 只检查结构、页数和图片对象；10 月 7 日的中文字符映射修复仍位于试用交付包，没有进入生产 CLI。修复版已通过 PDF.js 22 页对照，Codex 实际面板仍未确认。其他待验收项见[使用状态](status.md)。

## 最新发布核对

以下版本来自本次官方 `releases/latest` 结果，表示查询时上游标为 Latest 的发布，不表示已安装或已适配。GitHub REST 查询部分受到匿名限流后，改由官方发布网页核对。

| 项目 | 本次确认的发布 | 对本项目的意义 |
|---|---|---|
| Docling | [v2.135.0](https://github.com/docling-project/docling/releases/tag/v2.135.0)，10 月 7 日发布 | 文档格式与 PDF/OCR 转换持续维护 |
| MinerU | [4.0.10](https://github.com/opendatalab/MinerU/releases/tag/mineru-4.0.10-released)，9 月 29 日发布 | 应按 4.x 的接口、依赖和许可证评估 |
| GROBID | [0.9.1](https://github.com/grobidOrg/grobid/releases/tag/0.9.1) | 论文结构与参考文献解析候选 |
| Better BibTeX | [v9.0.71](https://github.com/retorquere/zotero-better-bibtex/releases/tag/v9.0.71) | 接入时核对 Zotero 版本和引用键迁移 |
| PaperQA | [v2026.08.12](https://github.com/Future-House/paper-qa/releases/tag/v2026.08.12) | 已使用日期版本；PaperQA2 名称不是当前包版本 |
| MarkItDown | [v0.1.8](https://github.com/microsoft/markitdown/releases/tag/v0.1.8) | 轻量格式转换候选 |
| PaddleOCR | [v3.7.0](https://github.com/PaddlePaddle/PaddleOCR/releases/tag/v3.7.0) | 中文 OCR 与复杂版面解析候选 |
| NJUThesis | [v1.5.1](https://github.com/nju-lug/NJUThesis/releases/tag/v1.5.1) | 当前已适配同一版本，本次未发现更新的 Latest 发布 |

## 集成选择

P0 是当前交付故障的预防工作；P1 是建议先接的能力；P2 在实际材料出现相应需要时接入。多个 PDF 解析器有较大重叠，先用同一批材料比较，再选默认工具。

| 优先级 | 工具及官方来源 | 能补的能力 | 建议接法与限制 |
|---|---|---|---|
| P0 | [PDF.js](https://mozilla.github.io/pdf.js/examples/) + 已有 pypdf | 提前发现浏览器中文缺字和文字提取问题 | 扩展现有 PDF 检查：记录字体映射并实际渲染关键页；缺少 ToUnicode 是风险信号，不能单凭它判所有 PDF 都不可用。复用已验证的修复方法并保留原件 |
| P1 | [OpenAlex API](https://help.openalex.org/api/) | 按主题、作者、年份发现论文并展开引用关系 | 官方 API 输出候选 JSON、查询条件、检索时间和来源；按 DOI 去重。候选记录不证明论文支持稿件中的结论 |
| P1 | [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | 核对 DOI、题名、作者、年份与发表信息 | 元数据差异交给作者确认，不静默覆盖已有文献。更新关系可辅助检查更正/撤稿，未查到记录不等于不存在问题 |
| P1 | [Zotero + Better BibTeX](https://retorque.re/zotero-better-bibtex/) | 统一文献与引用键，自动导出 BibLaTeX | 消费指定集合导出的 `.bib`，保持已有 citekey；飞书引用映射、Biber 使用同一份记录。已连接本机真实集合，自动导出、引用键保持、Crossref 核对和整篇编译通过 |
| P1 | [Docling](https://github.com/docling-project/docling) | PDF/Office 文档解析为文本、表格等结构，提供 OCR | 首选试验对象：独立环境运行官方 CLI，保存原件、JSON 和 Markdown；用 [ProvenanceItem](https://github.com/docling-project/docling-core/blob/main/docling_core/types/doc/document.py) 的页码和框坐标关联证据。书目专用解析仍需单独验证 |
| P2 | [MinerU](https://github.com/opendatalab/MinerU) | 复杂文档解析及按页、块定位的阅读 | 4.x 有 CLI/SDK/API 和多种解析档位，适合与 Docling 比较中文扫描件、公式和表格。先验证本机资源、目标档位与许可证条件 |
| P2 | [GROBID](https://github.com/grobidOrg/grobid) | 论文标题作者、参考文献、正文引文及坐标提取 | 针对英文论文书目与引文结构，以独立服务输出 TEI/XML；需要 Java/服务环境，部分模型另有依赖，不放进核心 Python 包 |
| P2 | [Semantic Scholar Recommendations](https://api.semanticscholar.org/api-docs/recommendations) | 根据种子论文寻找相关论文 | 补充召回；先核对端点 key 和配额，与 OpenAlex 共用候选池和去重规则 |
| P2 | [Unpaywall API](https://unpaywall.org/products/api) | 根据 DOI 查找开放获取版本 | 保存原始链接和版本信息，再决定下载；调用需联系邮箱，不能替代受限全文权限 |
| P2 | [PaperQA](https://github.com/Future-House/paper-qa) | 对选定论文集合问答并返回引文 | 等解析、引用键和证据定位稳定后再接；核对模型、嵌入服务与成本，答案引文仍须回到原页确认 |
| P2 | [MarkItDown](https://github.com/microsoft/markitdown) | 多格式材料快速转 Markdown；有官方 MCP | 轻量 Office 导入备选；复杂版面与页码证据单独验收。Docling 已满足时不增加重复默认路径 |
| P2 | [PaddleOCR / PP-StructureV3](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/pipeline_usage/PP-StructureV3.en.md) | OCR、版面、表格、公式和阅读顺序识别 | 用实际中文扫描页比较效果；模型和运行时较多，在选定解析器表现不足时再补入 |
| P2 | [Pandoc citeproc](https://pandoc.org/MANUAL.html) | Markdown、DOCX 等交换格式与 CSL 引用输出 | 适合额外 Word 交付；正式 NJUThesis PDF 继续走 Biber，飞书 block ID 与画板映射由现有流程保留 |
| 配套 | [uv tools](https://docs.astral.sh/uv/concepts/tools/) | 独立环境运行不同 Python 版本的工具 | 将重型解析器与 Python 3.9 核心分开，固定版本与参数，直接复用上游实现 |

**几个容易受旧教程影响的点：**

- [Docling 当前要求 Python 3.10 及以上](https://docling.ai/)。代码为 MIT，模型各有许可证；本机核心为 Python 3.9.6，建议独立安装。模型准备好后可本地处理材料。
- [Zotero 8 已有原生引用键](https://retorque.re/zotero-better-bibtex/)，BBT 已停止支持 Zotero 7 的后续更新。读取旧 BBT 数据库会遇到迁移问题，优先用受支持的导出接口。
- [OpenAlex 允许无 key 的基本查询](https://help.openalex.org/api/authentication/)，免费 key 可提高日预算；批量工作需处理预算、分页和 429，不能假定无限免费。
- [MinerU 当前许可证](https://github.com/opendatalab/MinerU/blob/master/LICENSE.md)基于 Apache 2.0 并附有其他条件，不能沿用旧文章中的 AGPL 或纯 Apache 2.0 描述。

## 接入顺序

1. **补交付检查。** 将中文 PDF 修复经验纳入 `inspect-pdf` 和交付流程。原件与修复件分别留存；PDF.js 渲染、文字提取和 Codex 面板验收分别记录。
2. **补文献发现与核对。** OpenAlex 搜索生成候选，Crossref 核对 DOI 元数据。先支持少量结果、超时、缓存和明确失败提示；候选经过选择后才进入写作材料。
3. **固定引用来源。** 从指定 Zotero 集合导出 BibLaTeX，保存 DOI 到 citekey 的映射，复用飞书引用转换与 `check`。没有 Zotero 时先支持作者提供的 `.bib`。
4. **补原文阅读。** 独立环境试用 Docling，保留文件哈希、解析器版本、页码和坐标。用中文扫描稿、英文双栏论文以及含表格/公式的页面，与 MinerU 按需比较。实际验收后才选默认解析器。
5. **按需求扩展。** 引用结构需要更精细时加 GROBID，全文集合问答明确需要时再加 PaperQA。检索、解析、问答共用来源记录。

建议直接调用上游 CLI/API，核心只处理输入、结果文件与来源对应。解析流程应同时交付原件、结构化结果和可阅读文本；只输出 Markdown 会丢掉核对证据所需的信息。此处为集成方案，本次没有新增命令或安装解析器。

## 本次验证与后续验收

实际执行的两个公开接口均为匿名只读请求，没有上传私人材料，没有创建账号或设置 API key：

| 检查 | 结果 | 证明范围 |
|---|---|---|
| Crossref：查询 `10.1038/nature14539` | HTTP 200，返回题名 Deep learning 与匹配 DOI | 单条元数据接口可连接，不证明批量去重、撤稿覆盖或引文含义 |
| OpenAlex：搜索 `document parsing`，取 3 条 | HTTP 200，返回 3 条候选及 ID、DOI、年份 | 基础检索可连接，不证明召回质量或中文覆盖 |
| `thesis --help`、`doctor`、`njucli tex --help` | 15 个命令；主要依赖可定位；NjuCLI 13 个业务子命令 | 入口与依赖，不证明登录、线上编译或页面效果 |
| 上游发布页 | 8 个项目的 Latest 版本完成核对 | 当前调研快照，接入时仍需固定并验证具体版本 |

接口回执和本机盘点见[本次记录](../output/integration-survey-20261008/)。文档使用本地链接检查和接口实际调用验证，未新增自动测试套件。

后续验收应覆盖：题名和 DOI 冲突、已有引用键保持、中文双栏和扫描件阅读顺序、表格与公式正确性、证据页码定位，以及失败时保留原始材料。Codex 实际面板也需重新确认中文页面，该项不能由结构检查或其他 PDF 阅读器代替。
