# 依赖

| 功能 | 依赖 |
|---|---|
| 写作与审阅 | 能读取材料的 AI 助手；纯写作无需 Python 或 TeX |
| CLI 与文件处理 | Python 3.9 以上、pypdf |
| 数据绘图 | 可选 Matplotlib、图中文字所需字体 |
| 结构绘图 | 按任务选择 Archify、飞书画板或已有建模工具 |
| 本地 TeX 编译 | latexmk、XeLaTeX、模板宏包与字体；文献按工程需要使用 Biber |
| 飞书材料 | Lark CLI 与相应 Lark Skill |
| 文风校准 | 配套 thesis-calibrate Skill、作者样文、Lark CLI 评论读写权限 |
| 本地重复比对 | 可选 RapidFuzz；只覆盖指定资料 |
| 南大平台 | 用户已有的 NjuCLI 与登录态 |
| DOI 与引用库 | 可选 Pybtex；OpenAlex / Crossref 官方 API；Zotero + Better BibTeX 可选本机导出 |
| 中文 PDF 预览 | Node.js、PDF.js、@napi-rs/canvas；已有 pypdf 用于映射检查与修复副本 |
| 原文解析 | 独立 Python 3.11 + Docling[rapidocr]；模型与核心 CLI 分开 |

`thesis doctor` 只查看依赖能否定位，不核验登录、宏包或版式。实际编译以本次 PDF 与完整日志为准。

## 来源

- [NJUThesis](https://github.com/nju-lug/NJUThesis)：模板，自动组稿支持 v1.5.1 标准样例，LPPL-1.3c+。使用作者提供的工程，不复制模板实现。
- Archify：结构图，使用已安装 Skill，MIT。
- Matplotlib：数据图与 SVG、PDF 原生导出，PSF-based license。
- [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz)：MIT，本地字符串相似度；算法说明见 [fuzz.ratio](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html#rapidfuzz.fuzz.ratio)。不提供论文数据库。
- [nju-se-thesis-self-check](https://github.com/dongshao/nju-se-thesis-self-check)：送审前自查的外部可选 Skill，当前未找到许可证，未随工具集分发。
- Zotero 与 Better BibTeX：使用官方导出文件或本机 pull export，保留引用键；自动同步见 [接入说明](integrations.md)。
- [Docling](https://github.com/docling-project/docling)：官方 CLI 本地解析，代码 MIT，模型许可证另查。
- [PDF.js](https://github.com/mozilla/pdf.js)：Apache-2.0，负责实际页面对照；@napi-rs/canvas 使用 MIT。
- [Pybtex](https://pybtex.org/)：MIT，解析 BibTeX；不重写作者原文献。
