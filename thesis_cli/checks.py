"""Read-only checks for static TeX dependencies and PDF structure."""

import math
import re
from pathlib import Path

from .texproject import _bib_entries, _split_options


COMMAND = re.compile(r"\\([A-Za-z@]+)\*?|\\.", re.S)
CITES = set("cite citep citet citealp citealt parencite textcite autocite supercite footcite smartcite fullcite footfullcite citeauthor citetitle citeyear citeyearpar nocite".split())
MULTICITES = set("cites parencites textcites autocites footcites smartcites supercites".split())
REFS = set("ref eqref pageref autoref cref cpageref vref nameref".split())
SKIP_DIRS = {"build", "dist", "output", "release", "node_modules", "__pycache__"}


def _code(text):
    result, position = list(text), 0
    while position < len(text):
        end = position
        if text[position] == "%":
            end = text.find("\n", position)
            end = len(text) if end < 0 else end
        elif text[position] == "\\":
            env = re.match(r"\\begin\s*\{(verbatim\*?|Verbatim|lstlisting|minted|comment)\}", text[position:])
            verb = re.match(r"\\(?:verb\*?|lstinline(?:\[[^\]\n]*\])?)([^A-Za-z\s])", text[position:])
            if env:
                closing = "\\end{" + env.group(1) + "}"
                found = text.find(closing, position + env.end())
                end = len(text) if found < 0 else found + len(closing)
            elif verb:
                found = text.find(verb.group(1), position + verb.end())
                if found >= 0 and "\n" not in text[position:found]:
                    end = found + 1
            if end == position:
                position += 2
                continue
        if end > position:
            result[position:end] = ["\n" if char == "\n" else " " for char in text[position:end]]
            position = end
        else:
            position += 1
    return "".join(result)


def _argument(text, position, opening="{", closing="}"):
    while position < len(text) and text[position].isspace():
        position += 1
    if text[position:position + 1] != opening:
        return None, position
    start, depth = position + 1, 1
    position += 1
    while position < len(text):
        if text[position] == "\\":
            position += 2
            continue
        if text[position] == opening:
            depth += 1
        elif text[position] == closing:
            depth -= 1
            if not depth:
                return text[start:position], position + 1
        position += 1
    return None, position


def check_tex(source, bibliography=None):
    source = Path(source).resolve()
    if not source.exists() or (source.is_file() and source.suffix.lower() != ".tex"):
        raise ValueError("需要现有 TeX 文件或目录：" + str(source))
    root = source if source.is_dir() else source.parent
    errors, warnings, files, commands = [], [], {}, []
    labels, citations, references, bibkeys, bibfiles = {}, [], [], {}, set()

    def issue(target, path, line, message):
        target.append({"file": str(path), "line": line, "message": message})

    def resolve(value, suffixes, path, line):
        if not value or re.search(r"[\\{}#$~\x00]", value):
            issue(warnings, path, line, "未解析动态路径：" + value)
            return None
        candidate = root / value.strip()
        options = [candidate] if candidate.suffix else [candidate.with_suffix(suffix) for suffix in suffixes]
        return next((item.resolve() for item in options if item.is_file()), options[0])

    queue = [source] if source.is_file() else sorted(
        path for path in source.rglob("*.tex")
        if not any(part.startswith(".") or part in SKIP_DIRS for part in path.relative_to(source).parts))
    if source.is_dir():
        issue(warnings, source, None, "目录模式合并扫描所有 TeX；多个主文档应分别指定入口检查")
    if not queue:
        issue(errors, source, None, "没有找到 TeX 文件")
    while queue:
        path = queue.pop(0).resolve()
        if path in files:
            continue
        try:
            code = _code(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            issue(errors, path, None, str(exc))
            continue
        files[path] = code
        for match in COMMAND.finditer(code):
            name = (match.group(1) or "").lower()
            line, position = code.count("\n", 0, match.start()) + 1, match.end()
            while True:
                optional, next_position = _argument(code, position, "[", "]")
                if optional is None:
                    break
                position = next_position
            value, end = _argument(code, position)
            if name in {"input", "include"}:
                if value is None:
                    issue(warnings, path, line, "未解析 \\" + name + "，需要静态花括号参数")
                else:
                    target = resolve(value, [".tex"], path, line)
                    if target and target.is_file():
                        queue.append(target)
                    elif target:
                        issue(errors, path, line, "缺少输入文件：" + str(target))
            elif name in CITES | MULTICITES | REFS | {"label", "bibitem"}:
                while True:
                    if value is None or any(re.search(r"[\\{}#\s]", key.strip()) for key in value.split(",")):
                        issue(warnings, path, line, "未解析 \\" + name + " 的静态键")
                        break
                    for key in value.split(","):
                        key = key.strip()
                        if name == "nocite" and key == "*":
                            continue
                        if not key:
                            issue(errors, path, line, "空引用键")
                        elif name in {"label", "bibitem"}:
                            index = labels if name == "label" else bibkeys
                            if key in index:
                                issue(errors, path, line, "重复键 " + key + "，首次出现于 " + str(index[key]))
                            index[key] = str(path) + ":" + str(line)
                        else:
                            (citations if name in CITES | MULTICITES else references).append((key, path, line))
                    if name not in MULTICITES:
                        break
                    position = end
                    for _ in range(2):
                        optional, next_position = _argument(code, position, "[", "]")
                        if optional is not None:
                            position = next_position
                    value, end = _argument(code, position)
                    if value is None:
                        break
            elif name in {"addbibresource", "bibliography", "includegraphics", "graphicspath"}:
                commands.append((name, value, path, line))
            elif name == "njusetup" and re.match(r"\s*\[\s*bib\s*\]", code[match.end():]):
                for item in _split_options(value or ""):
                    key, _, resource = item.partition("=")
                    if key.strip() == "resource":
                        commands.append(("bibliography", resource.strip().strip("{}"), path, line))
            elif name in {"import", "subimport", "inputiffileexists", "includeonly", "externaldocument"}:
                issue(warnings, path, line, "未展开 \\" + name + "；请显式提供文献文件或检查编译日志")
    graphic_dirs = [""]
    for name, value, path, line in commands:
        if name == "graphicspath" and value is not None:
            graphic_dirs += re.findall(r"\{([^{}]*)\}", value)
    for name, value, path, line in commands:
        if name == "graphicspath":
            continue
        if value is None:
            issue(warnings, path, line, "未解析 \\" + name + " 的参数")
            continue
        if name == "includegraphics":
            candidates = [resolve(folder + value, [".pdf", ".png", ".jpg", ".jpeg", ".eps"], path, line) for folder in graphic_dirs]
            if any(candidates) and not any(item and item.is_file() for item in candidates):
                issue(errors, path, line, "缺少插图：" + value)
        else:
            for item in value.split(","):
                target = resolve(item, [".bib"], path, line)
                if target:
                    bibfiles.add(target)
                    if not target.is_file():
                        issue(errors, path, line, "缺少文献文件：" + str(target))
    for item in bibliography or []:
        bibfiles.add((root / item).resolve())
    for path in sorted(bibfiles):
        try:
            text = path.read_text(encoding="utf-8")
            for kind, body in _bib_entries(text):
                if kind in {"comment", "string", "preamble"}:
                    continue
                key, separator, _ = body.partition(",")
                key, line = key.strip(), text.count("\n", 0, text.find(body)) + 1
                if not separator or not key or re.search(r"[\s{}(),=\\]", key):
                    issue(errors, path, line, "无效 BibTeX 条目键")
                elif key in bibkeys:
                    issue(errors, path, line, "重复文献键：" + key)
                else:
                    bibkeys[key] = str(path) + ":" + str(line)
        except (OSError, UnicodeError, ValueError) as exc:
            issue(errors, path, None, str(exc))
    for entries, known, description in [(citations, bibkeys, "未定义文献键："), (references, labels, "未定义标签：")]:
        for key, path, line in entries:
            if key not in known:
                issue(errors, path, line, description + key)
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "files": [str(path) for path in sorted(files)], "bibliography": [str(path) for path in sorted(bibfiles)],
            "counts": {"citations": len(citations), "labels": len(labels), "references": len(references)},
            "limitations": ["仅扫描静态命令，不执行宏、条件分支或包代码，不能代替编译", "相对路径以指定入口所在目录为基准", "不判断文献真实性、论证质量或视觉排版"]}


def inspect_pdf(path, preview=None, modules=None, pages=None, expected=None, timeout=180):
    from pypdf import PdfReader
    from pypdf.generic import ContentStream

    path = Path(path).resolve()
    result = {"ok": False, "file": str(path), "pages": 0, "image_objects": 0,
              "errors": [], "warnings": [], "limitations": ["结构检查不代表视觉验收；没有图像对象也不证明内容是有效矢量图"]}
    try:
        reader = PdfReader(str(path), strict=True)
        if reader.is_encrypted:
            raise ValueError("PDF 已加密")
        seen = set()

        def images(resources):
            xobjects = resources["/XObject"].get_object() if "/XObject" in resources else {}
            for reference in xobjects.values():
                obj = reference.get_object()
                identity = (getattr(reference, "idnum", None), getattr(reference, "generation", None)) if hasattr(reference, "idnum") else id(obj)
                if identity in seen:
                    continue
                seen.add(identity)
                if obj.get("/Subtype") == "/Image":
                    result["image_objects"] += 1
                elif obj.get("/Subtype") == "/Form":
                    result["image_objects"] += sum(operator == b"INLINE IMAGE" for _, operator in ContentStream(obj, reader).operations)
                    images(obj.get("/Resources", {}).get_object() if "/Resources" in obj else {})

        for page in reader.pages:
            box = [float(value) for value in page.mediabox]
            if not all(math.isfinite(value) for value in box) or box[2] <= box[0] or box[3] <= box[1]:
                raise ValueError("PDF 页面尺寸无效")
            contents = page.get_contents()
            if contents is not None:
                result["image_objects"] += sum(operator == b"INLINE IMAGE" for _, operator in contents.operations)
            images(page["/Resources"] if "/Resources" in page else {})
            result["pages"] += 1
        if not result["pages"]:
            raise ValueError("PDF 没有页面")
        from .pdfpreview import font_records, render_pdf
        result["structure_ok"] = True
        result["fonts"] = [{k: v for k, v in font.items() if k != "object"} for font in font_records(reader)]
        risky = [font for font in result["fonts"] if font["external_cmap_risk"]]
        result["portable_text_ok"] = not risky
        if risky:
            result["warnings"].append("中文 CID 字体缺少 ToUnicode，存在外部 CMap 依赖；预览可移植性待处理")
        result["ok"] = not risky
        result["preview"] = {"status": "not_run"}
        if preview:
            result["preview"] = render_pdf(path, preview, modules, pages, expected, timeout)
            result["ok"] = result["ok"] and result["preview"]["ok"]
    except Exception as exc:
        result["ok"] = False
        result["errors"].append(str(exc))
    return result
