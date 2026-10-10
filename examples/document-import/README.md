# 文档转换样例

这是合成的转换测试输入，不含真实论文结论。横图和纵图用于检查宽高比例，不是工程设计图。

`document.xml` 采用飞书完整 XML 导出结构。`assets.json` 把图片 token 和电子表格 token 映射到本地文件，路径相对映射文件所在目录。`values.csv` 是合成数据，第一行作为表头。转换保留单元格值，不恢复飞书公式、合并或样式。

图源为 `draw.py`，`assets/` 保留对应 SVG 和 PDF。只需重新绘图时安装 `.[plots]`，将旧图移到备份目录后运行 `python examples/document-import/draw.py`。

运行转换：

```bash
thesis import-doc examples/document-import/document.xml /path/to/converted --assets examples/document-import/assets.json
```

也可调用 Python 接口：

```python
from thesis_cli.documents import import_document

report = import_document(
    "examples/document-import/document.xml",
    "/tmp/thesis-document-import-example",
    assets="examples/document-import/assets.json",
)
```

输出包含 `document.tex`、`preamble.tex`、原始输入、素材副本和 `report.json`。输出目录必须尚不存在，避免覆盖人工修改。把输出文件与 `assets` 目录放在 TeX 主文件所在目录，在导言区引入 `preamble.tex`，正文引入 `document.tex`。中文主工程需要 XeLaTeX 和中文字体配置。

报告的 `ok` 只表示受支持内容完成转换，不表示完成编译或排版验收。图片按实际文件宽高等比缩放，同时限制页面宽度与高度。长表使用 `longtable` 重复表头；含表格的分栏会改为纵向排列并报告提醒。

真实文档使用 `lark-cli docs +fetch --doc <链接> --doc-format xml --detail full --as user` 的完整 JSON 响应作为输入。导出响应中的文档 ID、revision 和 reference_map 会保留。图片、画板和电子表格需分别导出到本地，本命令不联网获取素材。

引用可在映射中写成 `"引用ref": {"bibkey": "文献键"}`，需自行提供并核验相应 BibTeX 条目。没有映射的引用、缺少素材、合并表格和不支持的块会产生带块 ID 的错误，并在 TeX 中留下可见标记。原始 XML 始终保留，不把错误内容当作转换成功。
