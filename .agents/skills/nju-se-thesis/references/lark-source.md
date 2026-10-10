# 飞书材料

## 依赖

使用 `$lark-doc` 和 `lark-cli`，显式指定 `--as user`，直接调用目标命令。收到登录或权限错误时，再按 `$lark-shared` 处理该错误。

## 读取

1. 根据文档链接或 token 确定提取主题和目标章节。
2. 使用 `lark-cli docs +fetch --doc "<URL或token>" --as user` 获取材料，按 `$lark-doc` 选择 `--scope` 局部读取。
3. 将采用的材料登记到 `sources/lark-sources.yaml`，记录来源、读取时间、用途和目标章节。
4. 区分会议记录、个人意见和正式制度，不将未经确认的讨论写成事实。
5. 文档含电子表格或多维表格时，按对应 Lark Skill 读取实际内容。
6. 修改材料来源文档须经用户明确要求。内容编辑使用 `$lark-doc`，评论和权限管理使用 `$lark-drive`。

工具集自身的变更按根目录 `AGENTS.md` 和 `.lark-sync.yaml` 更新报告当前章节，与论文材料读取分开。

论文公开、送审或提交前，检查内部材料的脱敏、授权和引用方式。

## 转换

整篇转换需要 `docs +fetch --detail full --doc-format xml` 的完整响应，保留 `reference_map` 与版本号。局部 `fragment` 或 `excerpt` 不能冒充完整文档。输出原文副本，不回写来源文档。

下载正文图片和画板时按 Lark 对应 Skill 操作。画板尽量同时导出原始节点或 Mermaid、PlantUML 源与 SVG；SVG 仅是外观快照时，不声称恢复了可编辑模型。TeX 插图使用转换后的 PDF 或原始 PNG/JPEG。

附件映射使用 JSON，键为原文块 ID、token、ref 或 src，值为相对映射文件的本地路径。引用可写为 `{"bibkey": "key"}`，仍须核验文献并提供相应 BibTeX。

```json
{
  "wide-figure": "assets/wide.pdf",
  "sheet-token": "values.csv",
  "citation-block": {"bibkey": "verified-paper"}
}
```

```bash
thesis import-doc ./export.json ./converted --assets ./assets.json --source-url '原文链接'
```

普通表格转为可跨页 `longtable`，图片等比限宽限高，简单分栏转为 `minipage`。合并表格尚需人工处理，宽表需检查列宽。电子表格先读取完整选定范围再导出 CSV；当前转换仅采用值，首行作表头，不保留公式、样式和合并关系。缺少资源或不支持元素会写入 `report.json`，包含块 ID，正文保留可见标记。

重导出到新目录，再将差异应用到生成工程。作者在飞书修正文稿，代理处理路径、宏包和编译。当前不做双向同步，也不承诺任意文档无损转换。
