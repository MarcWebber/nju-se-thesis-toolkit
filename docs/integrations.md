# 文献与 PDF 工具

从 0.5.0 起，工具集有 19 个命令。新增 `literature-search`、`reference-check`、`bibliography` 和 `read-paper`；`inspect-pdf` 和 `build` 增加中文字体与 PDF.js 渲染检查。原有写作和转换流程沿用。

## 安装

本机已配置核心环境、PDF.js 与 Docling，直接使用 `.venv/bin/thesis`。在新环境中分别安装，避免把 Docling 的模型依赖放入核心 Python 环境：

```bash
uv pip install --python .venv/bin/python '.[references]'
npm install --prefix .tools/pdfjs --save-exact --no-audit --no-fund --ignore-scripts pdfjs-dist@5.6.205 @napi-rs/canvas@0.1.96
uv venv --python 3.11 .tools/docling
uv pip install --python .tools/docling/bin/python 'docling[rapidocr]==2.135.0'
.venv/bin/thesis doctor
```

核心仍支持 Python 3.9。PDF.js 使用 Node.js；Docling 使用独立 Python 3.11 环境。Docling 首次处理 PDF/扫描件会下载公开模型，本机推理，不上传论文。实际用到的模型快照保存在 `.tools/docling-cache/huggingface/`，OCR 模型由上游保存在独立环境内。

工具从当前目录向上查找 `.tools/`。跨目录使用时，可用 `THESIS_DOCLING` 指定 Docling 可执行文件、`THESIS_PDFJS_MODULES` 指定包含 `pdfjs-dist` 和 `@napi-rs/canvas` 的 node_modules 目录。重型依赖和模型没有打进 wheel。

## 中文 PDF 检查

```bash
thesis inspect-pdf paper.pdf
thesis inspect-pdf paper.pdf --preview-dir checks/paper --expect-text 学位论文
thesis inspect-pdf paper.pdf --preview-dir checks/selected --pages 1,9-10
```

默认结构检查会列出字体嵌入、ToUnicode、CID 字符集和所在页。中文 CID 字体使用 Identity 编码而没有 ToUnicode 时，报告外部 CMap 依赖风险并返回 2；`structure_ok` 与 `portable_text_ok` 分别表示结构和文字可移植性。它不把该风险等同于 PDF 文件损坏。

指定 `--preview-dir` 后，PDF.js 对所选页面分别在有外部 CMap 和无外部 CMap 的配置下渲染，比较文字和像素。默认检查全部页面，保存 PNG、日志和 `preview.json`；有差异、替代字符或缺少 `--expect-text` 指定文字时返回 2。预期文字匹配忽略排版空白，需在至少一个选中页面检出。输出目录需为新目录，避免覆盖上次证据。对照不能发现两种渲染共同存在的问题，仍需看页；也不代表 Codex 面板已验收。

对已确认属于 Adobe GB1 / Identity-H 的字体，可用维护中的 Adobe 映射生成新副本，其他字体不会套用该映射：

```bash
thesis inspect-pdf paper.pdf --repair-to paper-fixed.pdf \
  --cmap /path/to/Adobe-GB1-UCS2 --preview-dir checks/fixed
```

映射取自 TeX Live 随附的 Adobe mapping-resources-pdf，转交映射时同时保留其许可证。命令拒绝覆盖原 PDF，保留原文件和映射哈希，并强制指定预览目录检查修复结果。本项目已保存的样本映射位于 `output/pilot-20261002/delivery/resources/Adobe-GB1-UCS2`，许可证在同目录。

`build` **默认执行 PDF.js 全页检查**，检查不通过时整条命令返回 2；缺少运行依赖也会明确失败，不静默跳过。给出 `--cmap` 时，会为适用字体生成修复副本再检查；原编译 PDF 保留在 compiled 目录。

```bash
thesis build paper/main.tex builds/review --cmap /path/to/Adobe-GB1-UCS2
```

确实只需编译时可显式使用 `--skip-preview`；报告记录跳过状态，该结果不能作为页面验收。编译副本不复制 `.tools`、`.venv`、`node_modules`、`.git` 和 Python 缓存。

## 文献发现与核对

```bash
thesis literature-search 'document parsing' --year 2025-2026 --limit 10 --output literature/search
thesis literature-search --references 10.1038/nature14539 --limit 10 --output literature/references
thesis literature-search --cites 10.1038/nature14539 --limit 10 --output literature/cited-by
thesis reference-check 10.1038/nature14539 --output literature/doi
thesis reference-check references.bib --output literature/check
```

`literature-search` 调用 [OpenAlex](https://help.openalex.org/api/)，按 DOI 去重，保存题名、作者、年份、来源、引用关系、检索条件和原始响应。`--references` 是指定论文引用的文献，`--cites` 是引用指定论文的文献。默认取 10 条，最多 100 条，不自动遍历整个引用图。可通过 `OPENALEX_API_KEY` 环境变量传 key；key 只进入请求头，不写入结果文件。429 和临时服务错误最多重试两次。

`reference-check` 调用 [Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)，检查 DOI、题名、作者姓氏和年份。`.bib` 中没有 DOI 的条目保留为未核验，不猜测标识符；元数据不匹配标记为待复核，返回 2，不修改原文献。Crossref 没有匹配也可能是注册机构覆盖问题，不能直接认定文献不存在。更新关系只提供线索，不能宣称完整撤稿审查。以上命令取得的是元数据，不证明论文支持正文中的论断。

## Zotero 与引用键

```bash
thesis bibliography /path/to/exported.bib literature/library
thesis bibliography 'http://127.0.0.1:23119/better-bibtex/collection?/LIBRARY_ID/COLLECTION_KEY.biblatex' literature/library-new --existing references.bib
```

第一种输入来自作者已有 `.bib` 或 Zotero/Better BibTeX 的自动导出文件。第二种 URL 应从 Zotero 目标集合的 Better BibTeX 导出菜单取得，或通过官方 JSON-RPC 的 `user.groups(true)` 读取真实文库 ID 与集合键，再按上式组合。`LIBRARY_ID` 和 `COLLECTION_KEY` 都须替换为实际值；本机文库 ID 为 `1`，使用 `0` 实际返回 404。接口仅接受本机 Better BibTeX URL，不跟随重定向。

导出得到 `references.bib`、`bibliography.json` 和 `citation-assets.json`。前者保留作者文本和引用键；JSON 保存来源、哈希和 DOI 到引用键的对应；素材映射可用于现有 `import-doc --assets`，已有图片映射应合并保留。同一 DOI 出现多个键、已有键被改名或移作其他 DOI 时，会保留输入快照并返回 2，不发布新的 references.bib。没有 DOI 的条目仍可通过原 URL 建立映射；其身份不能仅凭 DOI 自动核对。

自动更新使用 [Better BibTeX 的 Keep updated 导出](https://retorque.re/zotero-better-bibtex/exporting/auto/)，或者在每次编译前拉取目标集合：

```bash
thesis build paper/main.tex builds/latest \
  --bibliography-source /path/to/zotero-export.bib \
  --bibliography-target refs/references.bib \
  --cmap /path/to/Adobe-GB1-UCS2
```

`--bibliography-source` 也接受上述本机导出 URL。同步发生在新建的编译副本中，核对已有引用键后才编译，不改作者原工程或 Zotero 数据库。`--bibliography-target` 必须是副本内的 `.bib` 相对路径，并与主文件的 addbibresource 配置一致。

本机已安装 Zotero 10.0.6（`~/Applications/Zotero.app`）与 Better BibTeX 9.0.71，集合“论文工具集 · 公开参考文献”中已有两篇通过 DOI 导入的真实论文。持续自动导出到 `references/zotero-public.bib`；新增第二篇论文后，文件自动从 1 条更新为 2 条，第一篇引用键保持一致。Zotero 运行时可直接读取当前集合：

```bash
.venv/bin/thesis bibliography 'http://127.0.0.1:23119/better-bibtex/collection?/1/9YPYBFVH.biblatex' output/library-current
```

Zotero 关闭时可读取最近一次自动导出的 `.bib`。这是本机文库，云端账号同步尚未配置。自动导出使用 [BBT 官方 API](https://retorque.re/zotero-better-bibtex/exporting/json-rpc/) 的 `autoexport.add`；实际回执、导出前后文件、Crossref 核对与整篇编译保存在 `output/real-delivery-20261008/`。

## 原文解析

```bash
thesis read-paper paper.pdf reading/paper --pages 9-10
thesis read-paper scan.png reading/scan
thesis read-paper paper.pdf reading/fast --pipeline native --no-ocr
```

命令直接调用 [Docling CLI](https://docling-project.github.io/docling/reference/cli/)，默认 standard 管线，启用中文 RapidOCR 与表格解析；native 模式用于已有文字的快速读取，须显式禁用 OCR。接受本地文件，避免把作者材料默认发往远程服务。页码从 1 开始，输出保持原 PDF 页号。

每次结果包含原文件副本、来源 SHA-256、Docling 版本和命令、原始 JSON、Markdown、图件、日志及 `evidence.json`。每条证据保存原始 item 引用、页码、框坐标及坐标原点；完整表格单元格仍保存在原始 JSON 中。源文件本身是扫描图片时，页号 1 指该图片，不能冒充它在其他 PDF 中的页码。

`ok=true` 表示转换与定位输出成功，`quality_review_required=true` 表示仍需原页核对。此次扫描样本出现个别中文误识别和标题顺序差异；跨页表在结构化结果中分成两个表块。不能将解析输出不经核对直接写入论文。失败时保留原件与日志，不生成虚假的成功记录。

## 验证记录

本次实际运行见 [integrations-20261008](../output/integrations-20261008/)，包括公开接口查询、引用键冲突、书目错误、问题 PDF 与修复版对照、22 页完整构建、中文双页表格解析及扫描页识别。未增加自动测试套件。
