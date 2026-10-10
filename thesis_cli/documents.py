"""Convert a saved Lark XML export into a traceable TeX fragment, without network access."""

import csv
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

from .files import digest, local, tex_text, write_json


PREAMBLE = "\\usepackage{graphicx,longtable,array,caption,amsmath,amssymb}\n"
MATH_COMMANDS = set("""frac dfrac tfrac sqrt sum prod int iint lim sin cos tan log ln exp
min max inf sup arg det left right big Big bigg Bigg cdot times div pm mp le leq ge geq
ne neq approx equiv sim to mapsto in notin subset subseteq supset supseteq cup cap
emptyset forall exists partial nabla infty alpha beta gamma delta epsilon varepsilon
zeta eta theta vartheta iota kappa lambda mu nu xi pi rho sigma tau upsilon phi varphi
chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega mathrm
mathbf mathit mathsf mathtt mathcal mathbb text operatorname overline underline hat
bar vec dot ddot underbrace overbrace ldots cdots vdots ddots quad qquad""".split())


def table_tex(rows, header_count=1, caption="", label=""):
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("表格为空或列数不一致")
    if label and not re.fullmatch(r"[A-Za-z][A-Za-z0-9:._-]*", label):
        raise ValueError("表标签需以字母开头，只使用字母、数字、冒号、点、下划线和连字符")
    columns = (r">{\raggedright\arraybackslash}p{\dimexpr\linewidth/" + str(len(rows[0]))
               + r"-2\tabcolsep\relax}") * len(rows[0])
    lines = [" & ".join(row) + r" \\" for row in rows]
    head = "\n".join(lines[:header_count])
    label_text = "\\label{" + label + "}" if label else ""
    title = ("\\caption{" + tex_text(caption) + "}" + label_text + "\\\\\n" if caption else
             "\\noalign{" + label_text + "}\n" if label else "")
    return ("\n\\begin{longtable}{" + columns + "}\n" + title +
            "\\toprule\n" + head + "\n\\midrule\n\\endfirsthead\n\\toprule\n" + head +
            "\n\\midrule\n\\endhead\n\\bottomrule\n\\endfoot\n" +
            "\n".join(lines[header_count:]) + "\n\\end{longtable}\n")


def csv_table(source, output, caption="", label="", landscape=False):
    source, output = Path(source).resolve(), Path(output).absolute()
    with source.open(encoding="utf-8-sig", newline="") as stream:
        rows = [[tex_text(cell).replace("\n", r"\newline{}") for cell in row] for row in csv.reader(stream)]
    text = table_tex(rows, caption=caption, label=label)
    if landscape:
        text = "\\begin{landscape}\n" + text + "\\end{landscape}\n"
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(source, output / "source.csv")
    (output / "table.tex").write_text(text, encoding="utf-8")
    (output / "preamble.tex").write_text("\\usepackage{longtable,booktabs,array}" +
                                        ("\n\\usepackage{pdflscape}" if landscape else "") + "\n", encoding="utf-8")
    report = {"source_sha256": digest(source), "rows": len(rows) - 1, "columns": len(rows[0]),
              "landscape": landscape, "compiled": False, "output": str(output)}
    write_json(output, "report.json", report)
    return report


def import_document(source, output, assets=None, source_url=""):
    """Read an XML/JSON file; create a new directory and return its conversion report.

    Asset entries map XML IDs, tokens or refs to relative local filenames. Citation
    entries use {"bibkey": "reference-key"}; the caller verifies the matching .bib.
    """
    source, output = Path(source).resolve(), Path(output).absolute()
    raw = source.read_bytes()
    content = raw.decode("utf-8-sig")
    metadata = {}
    if content.lstrip().startswith("{"):
        envelope = json.loads(content)
        if envelope.get("ok") is False:
            raise ValueError("飞书导出响应失败")
        metadata = envelope.get("data", {}).get("document", envelope.get("document", envelope))
        if not isinstance(metadata, dict):
            raise ValueError("导出响应 document 必须是对象")
        content = metadata.get("content")
        if not isinstance(content, str):
            raise ValueError("导出响应没有 XML content")
    if re.search(r"<!DOCTYPE|<!ENTITY", content, re.I):
        raise ValueError("不支持 XML DTD 或实体声明")
    content = re.sub(r"^\s*<\?xml[^?]*\?>", "", content)
    try:
        root = ET.fromstring("<document>" + content + "</document>")
    except ET.ParseError as error:
        raise ValueError("无法解析 XML：" + str(error)) from error
    mapping = json.loads(Path(assets).read_text(encoding="utf-8")) if assets else {}
    if not isinstance(mapping, dict):
        raise ValueError("素材映射必须是 JSON 对象")
    asset_root = Path(assets).resolve().parent if assets else source.parent
    output.mkdir(parents=True, exist_ok=False)
    (output / "assets").mkdir()
    (output / ("source.json" if metadata else "source.xml")).write_bytes(raw)
    if assets:
        shutil.copyfile(assets, output / "asset-map.json")
    references = metadata.get("reference_map", {})
    nodes = list(root.iter())[1:]
    ids = {node: node.get("id") or node.get("block-id") or "local-%d" % i
           for i, node in enumerate(nodes, 1)}
    report = {"source": str(source), "source_url": source_url,
              "source_sha256": digest(source), "document_id": metadata.get("document_id"),
              "revision_id": metadata.get("revision_id"), "reference_map": references,
              "blocks": [{"block_id": ids[n], "tag": n.tag} for n in nodes],
              "issues": [], "assets": [], "citation_keys": []}

    def issue(node, code, message, severity="error"):
        report["issues"].append({"block_id": ids[node], "tag": node.tag, "code": code,
                                 "severity": severity, "message": message})
        return r"\textbf{" + tex_text("[待处理 %s: %s]" % (ids[node], message)) + "}"

    def entry(node):
        attrs = dict(node.attrib)
        ref = attrs.get("ref")
        attrs.update(references.get(node.tag, {}).get(ref, {}) if isinstance(references, dict) else {})
        keys = [node.get("id"), node.get("block-id"), ref]
        keys += [attrs.get(key) for key in ("token", "src", "href", "url", "doc-id")]
        if node.tag == "cite":
            keys += [child.get("href") for child in node if child.tag == "a"]
        return next((mapping[key] for key in keys if key in mapping), None)

    def material(node, suffixes):
        value = entry(node)
        if not isinstance(value, str):
            return None, issue(node, "missing_asset", "缺少本地素材映射")
        try:
            path = local(asset_root, value)
            if path.suffix.lower() not in suffixes or not path.is_file():
                raise ValueError("素材格式或路径无效")
        except ValueError as error:
            return None, issue(node, "invalid_asset", str(error))
        name = "assets/media-%d%s" % (len(report["assets"]) + 1, path.suffix.lower())
        shutil.copyfile(path, output / name)
        report["assets"].append({"block_id": ids[node], "source": str(path), "path": name,
                                 "sha256": digest(path)})
        return name, ""

    def body(node, in_grid=False):
        text = tex_text(node.text or "")
        for child in node:
            text += render(child, in_grid) + tex_text(child.tail or "")
        return text

    def table(node, rows, header_count, in_grid):
        if in_grid:
            issue(node, "grid_table_layout", "分栏表格改为独占行，以保留跨页能力", "warning")
        try:
            return table_tex(rows, header_count)
        except ValueError as error:
            return issue(node, "invalid_table", str(error))

    def render(node, in_grid=False):
        tag = node.tag
        if tag in {"document", "column", "span", "figure"}:
            return body(node, in_grid)
        if tag in {"fragment", "excerpt"}:
            return issue(node, "partial_export", "输入是文档节选") + body(node, in_grid)
        if tag == "title" or re.fullmatch(r"h[1-9]", tag):
            level = 1 if tag == "title" else int(tag[1])
            command = ["section", "subsection", "subsubsection", "paragraph", "subparagraph"][min(level, 5) - 1]
            if level > 5:
                issue(node, "heading_depth", "五级以下标题统一为 subparagraph", "warning")
            return "\n\\" + command + ("*" if tag == "title" else "") + "{" + body(node) + "}\n"
        if tag in {"p", "li", "blockquote"}:
            value = body(node, in_grid)
            return ("\\item " + value + "\n" if tag == "li" else
                    "\n\\begin{quote}" + value + "\\end{quote}\n" if tag == "blockquote" else
                    value + "\n\n")
        if tag in {"b", "strong", "em", "i", "u", "code"}:
            command = {"b": "textbf", "strong": "textbf", "em": "emph", "i": "emph",
                       "u": "underline", "code": "texttt"}[tag]
            return "\\" + command + "{" + body(node, in_grid) + "}"
        if tag in {"ul", "ol"}:
            env = "enumerate" if tag == "ol" else "itemize"
            return "\n\\begin{" + env + "}\n" + body(node, in_grid) + "\\end{" + env + "}\n"
        if tag == "br":
            return r"\newline{}"
        if tag == "hr":
            return "\n\\par\\noindent\\rule{\\linewidth}{0.4pt}\\par\n"
        if tag == "pre":
            def code_text(element):
                return (element.text or "") + "".join(
                    ("\n" if child.tag == "br" else code_text(child)) + (child.tail or "") for child in element)
            code = code_text(node).expandtabs(4)
            errors = "".join(issue(child, "unsupported_element", "不支持代码内元素 " + child.tag)
                             for child in node.iter() if child.tag not in {"pre", "code", "br"})
            if any(len(line) > 100 for line in code.splitlines()):
                issue(node, "long_code_line", "代码长行需要检查换行和页宽", "warning")
            lines = [r"\noindent\strut " + tex_text(line).replace(" ", r"\ ") + r"\par" for line in code.splitlines()]
            caption = "\\textbf{" + tex_text(node.get("caption")) + "}\\par\n" if node.get("caption") else ""
            return "\n" + errors + caption + "{\\small\\ttfamily\\raggedright\n" + "\n".join(lines) + "\n}\n"
        if tag == "latex":
            formula = "".join(node.itertext())
            commands = re.findall(r"\\([A-Za-z]+|.)", formula)
            valid = all(c in MATH_COMMANDS or c in "{},;!: |" for c in commands)
            depth = 0
            for char in re.sub(r"\\[{}]", "", formula):
                depth += (char == "{") - (char == "}")
                valid = valid and depth >= 0
            if not valid or depth or re.search(r"[$%#&~]|\^\^|\\$", formula):
                return issue(node, "unsupported_formula", "公式包含不支持的 TeX 语法")
            return r"\(" + formula + r"\)"
        if tag in {"img", "whiteboard"}:
            name, error = material(node, {".pdf", ".png", ".jpg", ".jpeg"})
            if error:
                return error
            caption = node.get("caption", "")
            return ("\n\\begin{center}\\includegraphics[width=\\linewidth,height=0.72\\textheight,keepaspectratio]{" + name + "}" +
                    ("\\captionof{figure}{" + tex_text(caption) + "}" if caption else "") + "\\end{center}\n")
        if tag == "sheet" or (tag == "cite" and node.get("file-type") == "sheets"):
            name, error = material(node, {".csv"})
            if error:
                return error
            with (output / name).open(encoding="utf-8-sig", newline="") as stream:
                rows = [[tex_text(cell) for cell in row] for row in csv.reader(stream)]
            issue(node, "sheet_values_only", "CSV 仅保留单元格值，首行作为表头；公式、合并和样式未导入", "warning")
            return table(node, rows, 1, in_grid)
        if tag == "table":
            if any(c.get("rowspan", "1") != "1" or c.get("colspan", "1") != "1" for c in node.iter()):
                return issue(node, "merged_table", "合并单元格需要人工排版") + tex_text(" ".join(node.itertext()))
            invalid = [n for n in node if n.tag not in {"tr", "thead", "tbody", "colgroup"}]
            marker = "".join(issue(n, "unsupported_element", "不支持表格元素 " + n.tag) for n in invalid)
            if node.find("colgroup") is not None:
                issue(node, "table_column_widths", "表格列宽统一为等宽，需要检查宽表排版", "warning")
            row_nodes = [r for n in node for r in ([n] if n.tag == "tr" else n.findall("tr"))]
            rows = [[("{\\bfseries " + body(cell, in_grid) + "}" if cell.tag == "th" else body(cell, in_grid))
                     for cell in row if cell.tag in {"th", "td"}] for row in row_nodes]
            headers = len(node.findall("thead/tr")) or (int(any(c.tag == "th" for c in row_nodes[0])) if row_nodes else 0)
            return marker + table(node, rows, headers, in_grid)
        if tag == "grid":
            columns = list(node)
            if any(n.tag != "column" for n in columns) or not columns:
                return issue(node, "invalid_grid", "分栏结构无效") + body(node)
            if any(n.tag in {"table", "sheet", "grid"} or (n.tag == "cite" and n.get("file-type") == "sheets")
                   for c in columns for n in c.iter()):
                issue(node, "grid_layout", "含表格或嵌套分栏，转换为纵向排列", "warning")
                return body(node)
            try:
                ratios = [float(c.get("width-ratio", "1")) for c in columns]
                if any(r <= 0 for r in ratios) or not 0 < sum(ratios) < float("inf"):
                    raise ValueError()
            except ValueError:
                return issue(node, "invalid_grid", "分栏宽度无效") + body(node)
            parts = ["\\begin{minipage}[t]{%.5f\\linewidth}\n%s\\end{minipage}" %
                     (0.96 * ratio / sum(ratios), body(column, True)) for column, ratio in zip(columns, ratios)]
            return "\n\\par\\noindent\n" + "\\hfill\n".join(parts) + "\n\\par\n"
        if tag == "cite":
            value = entry(node)
            if isinstance(value, dict) and re.fullmatch(r"[A-Za-z0-9:._/-]+", str(value.get("bibkey", ""))):
                report["citation_keys"].append(value["bibkey"])
                return "\\cite{" + value["bibkey"] + "}"
            return issue(node, "unmapped_citation", "引用未映射到 BibTeX 键") + body(node)
        if tag == "a":
            value = body(node, in_grid)
            return value + (" " + tex_text(node.get("href", "")) if node.get("href") else "")
        return issue(node, "unsupported_element", "不支持元素 " + str(tag)) + body(node, in_grid)

    rendered = body(root)
    (output / "document.tex").write_text(rendered, encoding="utf-8")
    (output / "preamble.tex").write_text(PREAMBLE + "\\usepackage{booktabs}\n", encoding="utf-8")
    report["ok"] = not any(item["severity"] == "error" for item in report["issues"])
    report["compiled"] = False
    report["outputs"] = ["document.tex", "preamble.tex", "report.json", "assets/"]
    write_json(output, "report.json", report)
    return report
