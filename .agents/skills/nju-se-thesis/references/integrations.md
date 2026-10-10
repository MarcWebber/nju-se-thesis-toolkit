# 文献与 PDF 扩展

0.5.0 新增四个命令，详细参数使用命令帮助。复用上游接口与解析器，不将公开书目信息当作已读原文。

| 任务 | 入口与核对 |
|---|---|
| 文献发现 | `thesis literature-search QUERY --output DIR`；`--references DOI` 展开引用文献，`--cites DOI` 找引用该论文的工作；保留候选与原始响应 |
| DOI 核对 | `thesis reference-check DOI或BIB --output DIR`；题名、作者、年份差异回到原始来源确认，不静默覆盖 |
| 引用库 | `thesis bibliography SOURCE DIR --existing EXISTING_BIB`；SOURCE 为本地 .bib 或 Zotero 中取得的 Better BibTeX 本机导出 URL；原键变化或同 DOI 多键会阻断发布 |
| 原文读取 | `thesis read-paper FILE DIR --pages 1-4`；原件、JSON、Markdown、页码和框坐标全部保留，OCR 与表格输出逐页核对 |
| 中文预览 | `thesis inspect-pdf PDF --preview-dir DIR`；比较有无外部 CMap 的文字和像素，可用 `--expect-text` 核对文字 |
| 编译交付 | `build` 默认运行 PDF.js；`--cmap` 仅修复适用的 Adobe GB1 字体并保留原 PDF；缺少依赖不静默跳过 |

文献同步可通过 `build --bibliography-source SOURCE --bibliography-target refs/references.bib` 在编译副本中自动执行。Better BibTeX 的 Keep updated 或本机导出服务负责更新库；没有指定真实文献集合时，不宣称 Zotero 已连通。

核心文献解析需要可选依赖 `nju-se-thesis[references]`。PDF.js 与 Docling 安装在独立 `.tools` 中，也可用 `THESIS_PDFJS_MODULES`、`THESIS_DOCLING` 指定位置。推荐 Docling 2.135.0 的 rapidocr extra、Python 3.11，以及 PDF.js 5.6.205；具体本机验证记录以仓库 docs/integrations.md 为准。

`read-paper` 成功只代表转换与定位产物可用，仍需人工核对。扫描图片的页号 1 只表示该图片，不能伪称其在另一份 PDF 中的原始页码。未读全文时不扩写论文结论。PDF.js 对照也不能替代 Codex 实际面板和版式验收。
