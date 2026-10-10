# 模板组稿

已有完整 TeX 工程直接用 `thesis check main.tex` 和 `thesis build main.tex 输出目录`。需要将独立章节填入 NJUThesis 标准示例时再使用组稿工具。

```bash
thesis import-template template.zip 论文目录 --main njuthesis-sample.tex
thesis inspect-template 论文目录
thesis assemble 论文目录
```

导入的原工程在 `paper/`，源 ZIP 和哈希备份在 `.thesis/template/`。组稿输出 `build/project/` 和 `reports/assembly.json`，保留作者原工程。

## 文件

`thesis.json` 保存模板入口与作者信息。标题、英文标题、作者、院系、学位名称按普通文本填写；`manuscript.info` 补充 NJUThesis 原生 TeX 字段。

```json
{
  "title": "论文中文题名",
  "title_en": "English Title",
  "author": "作者姓名",
  "department": "软件学院",
  "degree": "电子信息硕士",
  "manuscript": {
    "format": "latex",
    "root": "paper",
    "main": "njuthesis-sample.tex",
    "bibliography": ["references.bib"],
    "type": "master",
    "degree": "professional",
    "info": {"student-id": "本人学号", "supervisor": "导师姓名,职称"}
  }
}
```

文献文件需要在模板中实际启用，不能只登记路径。未填写的信息和原附录仍沿用模板，组稿后核对封面、日期、导师和附录内容。类型配置在组稿副本中生效，不修改导入原件。

`outline.json` 只决定章节顺序与标题。每章正文位于 `paper/chapters/<id>.tex`，正文不包含 `\chapter` 或主文档环境。

```json
{"chapters": [{"id": "design", "title": "系统设计"}, {"id": "implementation", "title": "系统实现"}]}
```

`frontmatter.json` 保存原生 TeX 摘要、关键词和可选致谢：

```json
{
  "abstract_zh": "经作者核对的中文摘要正文。",
  "abstract_en": "The reviewed English abstract.",
  "keywords_zh": ["软件工程"],
  "keywords_en": ["software engineering"]
}
```

可选 `acknowledgements` 字段填写致谢正文，省略时保留模板内容。摘要正文不带环境，关键词不带关键词命令。

自动填充只识别 NJUThesis v1.5.1 标准示例区域，遇到未知正文停止。此时由代理阅读作者工程后局部修改，不能删除作者内容以满足自动识别条件。
