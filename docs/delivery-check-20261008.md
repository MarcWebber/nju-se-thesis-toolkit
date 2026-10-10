# 真实接入验收

2026-10-08 核对。当前工具集为 0.5.0，两个 Skill、19 个命令。本机已配置 Zotero 10.0.6、Better BibTeX 9.0.71、PDF.js 5.6.205 和 Docling 2.135.0。

## 结果

| 能力 | 实际操作与结果 | 证据 |
|---|---|---|
| Zotero 与 Better BibTeX | 官方应用已安装、插件已启用；在客户端通过 DOI 导入两篇真实论文；集合界面和原生引用键已查看 | [客户端版本](../output/real-delivery-20261008/zotero-ready.json)、[真实集合](../output/real-delivery-20261008/zotero-collections.json) |
| 自动导出与引用键 | BBT 持续导出到 references/zotero-public.bib；新增第二篇论文后文件从 1 条更新为 2 条，第一篇引用键保持 | [更新前](../output/real-delivery-20261008/autoexport-before.bib)、[更新后](../output/real-delivery-20261008/autoexport-after.bib)、[核对结果](../output/real-delivery-20261008/autoexport-verification.json) |
| 论文搜索与引用关系 | 本次直接请求 OpenAlex，关键词和年份查询返回 3 条、被引查询返回 2 条；引用文献展开的真实接口结果保留在上一轮 | [搜索](../output/real-delivery-20261008/openalex/literature.json)、[被引](../output/real-delivery-20261008/citations/literature.json)、[参考文献](../output/integrations-20261008/references/literature.json) |
| DOI 与书目核对 | 两篇 Zotero 实际导出文献的 DOI、题名、作者和年份均通过 Crossref 核对，均为 matched | [核对结果](../output/real-delivery-20261008/zotero-crossref/references-check.json) |
| 编译前刷新文献 | build 直接请求运行中的 Zotero 集合，加入已有试用稿的编译副本；XeLaTeX / Biber 完成，新增两条参考文献出现在第 19 页 | [编译书目](../output/real-delivery-20261008/build/bibliography/bibliography.json)、[构建结果](../output/real-delivery-20261008/build-result.json)、[文献页](../output/real-delivery-20261008/build/preview/page-019.png) |
| 中文预览检查 | 原问题 PDF 再次检出 5 个字体映射风险、封面对照失败，退出码 2；本次构建的 22 页修复 PDF 全页文字和像素对照通过；封面与参考文献页已目视核对 | [问题文件检查](../output/real-delivery-20261008/original-preview-result.json)、[22 页对照](../output/real-delivery-20261008/build/preview/preview.json)、[封面](../output/real-delivery-20261008/build/preview/page-001.png)、[PDF](../output/real-delivery-20261008/build/njuthesis-sample-preview.pdf) |
| Docling 原页证据 | 对本次 PDF 第 9–10 页运行 standard 管线，获得 12 条带原页号和边框坐标的记录，包括两个跨页表块 | [解析结果](../output/real-delivery-20261008/docling/paper.json)、[原页定位](../output/real-delivery-20261008/docling/evidence.json)、[正文与表格](../output/real-delivery-20261008/docling/converted/source.md) |

分发包同步更新并独立安装；从项目外运行安装后的 bibliography 命令，真实集合返回 2 条，引用键保持，输出与自动导出逐字节一致。见[包核对](../output/real-delivery-20261008/package.json)和[实际运行](../output/real-delivery-20261008/installed-bibliography-result.json)。

## 使用

Zotero 位于 `~/Applications/Zotero.app`。打开后选择“论文工具集 · 公开参考文献”，继续通过 DOI 添加文献，Better BibTeX 会更新 [zotero-public.bib](../references/zotero-public.bib)。当前两条引用键为 `lecunDeepLearning2015` 和 `guoDeepLearningVisual2016`。

在项目根目录使用以下命令，输出目录每次选一个新名称：

```bash
.venv/bin/thesis bibliography 'http://127.0.0.1:23119/better-bibtex/collection?/1/9YPYBFVH.biblatex' output/library-next
.venv/bin/thesis reference-check references/zotero-public.bib --output output/references-next
```

本机真实文库 ID 为 `1`，集合键为 `9YPYBFVH`。其他文库的地址应从客户端或 [BBT 官方 API](https://retorque.re/zotero-better-bibtex/exporting/json-rpc/) 获取。导出文件可供 Zotero 关闭时读取；HTTP 方式要求 Zotero 正在运行。云端账号同步尚未配置。

## 验收范围

本次证明了这两篇真实文献从 Zotero 导入、自动导出、元数据核对到参考文献排版的完整链路，以及该试用稿的字体检查与渲染结果。正式论文的研究内容、引文含义和学院格式由具体稿件另行核对。

扫描件的实际 OCR 已运行，保留 7 条定位；样本中存在中文段落漏识别和标题顺序差异，见[识别结果](../output/integrations-20261008/docling-scan/converted/source.md)。解析结果须对照原页，跨页表块仍保持分别记录。Codex 实际面板显示待确认。
