"""Package editable drawing sources and static vector exports without executing them."""

import json
from pathlib import Path
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET

from .files import digest, tex_text


SVG_TAGS = set("svg g defs symbol title desc metadata style path rect circle ellipse line "
               "polyline polygon text tspan textPath use clipPath mask pattern marker "
               "linearGradient radialGradient stop".split())
VECTOR_TAGS = {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon"}
URL = re.compile(r"url\(\s*(['\"]?)([^)'\"]+)\1\s*\)", re.I)
LABEL = re.compile(r"[A-Za-z][A-Za-z0-9:._-]*")


def _has_geometry(element, tag):
    def number(name):
        value = re.match(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", element.get(name, "0"))
        return float(value[0]) if value else 0

    if tag == "path":
        return bool(re.search(r"[LlHhVvCcSsQqTtAaZz]", element.get("d", "")))
    if tag in {"rect", "ellipse"}:
        first, second = ("width", "height") if tag == "rect" else ("rx", "ry")
        return number(first) > 0 and number(second) > 0
    if tag == "circle":
        return number("r") > 0
    if tag == "line":
        return number("x1") != number("x2") or number("y1") != number("y2")
    return len(re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", element.get("points", ""))) >= (6 if tag == "polygon" else 4)


def _check_svg(path):
    content = path.read_text(encoding="utf-8")
    content = re.sub(r'<!DOCTYPE\s+svg\s+PUBLIC\s+"-//W3C//DTD SVG 1\.1//EN"\s+'
                     r'"http://www\.w3\.org/Graphics/SVG/1\.1/DTD/svg11\.dtd"\s*>', "", content)
    if re.search(r"<!DOCTYPE|<!ENTITY|<\?(?!xml\s)", content, re.I):
        raise ValueError("SVG 不能包含外部实体或处理指令")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise ValueError("SVG 无法解析：" + str(exc)) from exc
    if root.tag not in ("svg", "{http://www.w3.org/2000/svg}svg"):
        raise ValueError("文件不是 SVG")
    references, identifiers, vectors = set(), set(), 0
    metadata = {child for element in root.iter()
                if element.tag in ("metadata", "{http://www.w3.org/2000/svg}metadata")
                for child in element.iter()}
    for element in root.iter():
        tag = element.tag.removeprefix("{http://www.w3.org/2000/svg}")
        if tag.rsplit("}", 1)[-1].lower() in {"script", "foreignobject", "image", "animate", "animatemotion", "animatetransform", "set"}:
            raise ValueError("SVG 不能包含脚本、图片或动画：" + tag)
        if any(key.rsplit("}", 1)[-1].lower().startswith("on") for key in element.attrib):
            raise ValueError("SVG 不能包含事件")
        if element in metadata:
            continue
        if tag not in SVG_TAGS:
            raise ValueError("SVG 不支持此元素：" + tag)
        identifiers.add(element.get("id", ""))
        vectors += tag in VECTOR_TAGS and _has_geometry(element, tag)
        values = [element.text or ""] if tag == "style" else []
        for key, value in element.attrib.items():
            name = key.rsplit("}", 1)[-1].lower()
            if name.startswith("on") or name in {"base", "src"}:
                raise ValueError("SVG 不能包含事件、外部资源或基址")
            if name == "href":
                if not value.startswith("#") or len(value) == 1:
                    raise ValueError("SVG 引用必须指向文件内的元素")
                references.add(value[1:])
            if name == "style" or "url" in value.lower():
                values.append(value)
        for value in values:
            value = re.sub(r"/\*.*?\*/", "", value, flags=re.S)
            if "\\" in value or "@" in value:
                raise ValueError("SVG 样式不能包含转义或外部 CSS 规则")
            if re.search(r"\b(?:animation|transition)(?:-[a-z-]+)?\s*:", value, re.I):
                raise ValueError("SVG 不能包含动画样式")
            for match in URL.finditer(value):
                target = match.group(2).strip()
                if not target.startswith("#") or len(target) == 1:
                    raise ValueError("SVG 样式不能引用外部资源")
                references.add(target[1:])
            if re.search(r"url\s*\(", URL.sub("", value), re.I):
                raise ValueError("SVG 包含无法识别的资源引用")
    if references - identifiers:
        raise ValueError("SVG 包含不存在的内部引用：" + ", ".join(sorted(references - identifiers)))
    if not vectors:
        raise ValueError("SVG 缺少矢量图元，不能仅交付图片或文字容器")
    return {"vector_elements": vectors, "validation": "静态自包含 SVG；图元可见性和排版待人工审阅"}


def _check_pdf(path):
    from .checks import inspect_pdf

    result = inspect_pdf(path)
    if not result["ok"]:
        raise ValueError("PDF 结构检查未通过：" + str(result["errors"]))
    if result["image_objects"]:
        raise ValueError("图件 PDF 含栅格图片，请从绘图源导出矢量 PDF")
    result.pop("file")
    return result


def _source_files(source):
    paths = [source, *source.rglob("*")] if source.is_dir() else [source]
    for path in paths:
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError("绘图源只接受普通文件和目录，不能包含符号链接：" + str(path))
    files = [path for path in paths if path.is_file()]
    if not files or not any(path.stat().st_size for path in files):
        raise ValueError("绘图源不能为空")
    return files


def package_figure(output, source, svg, pdf, caption="", label="", provenance=""):
    """Create a new deliverable directory; preserve every supplied source file."""
    output, source, svg = Path(output).absolute(), Path(source).absolute(), Path(svg).absolute()
    pdf = Path(pdf).absolute()
    if output.is_symlink() or output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("绘图交付目录必须不存在或为空，不覆盖已有内容")
    if source.is_dir() and (source.resolve() in output.resolve().parents or source.resolve() == output.resolve()):
        raise ValueError("交付目录不能位于绘图源目录内")
    if source.resolve() == Path(source.anchor):
        raise ValueError("绘图源不能是文件系统根目录")
    _source_files(source)
    for asset in (svg, pdf):
        if asset.is_symlink() or not asset.is_file():
            raise ValueError("绘图导出必须是普通文件：" + str(asset))
    if label and not LABEL.fullmatch(label):
        raise ValueError("图标签只能使用字母、数字、冒号、点、下划线和连字符，并以字母开头")
    checks = {"svg": _check_svg(svg), "pdf": _check_pdf(pdf),
              "visual_review": "pending", "source_reproducibility": "not_checked"}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".figure-", dir=output.parent) as temporary:
        package = Path(temporary) / "package"
        if source.is_dir():
            shutil.copytree(source, package / "source", symlinks=True)
        else:
            (package / "source").mkdir(parents=True)
            shutil.copy2(source, package / "source" / source.name)
        _source_files(package / "source")
        shutil.copy2(svg, package / "figure.svg")
        shutil.copy2(pdf, package / "figure.pdf")
        lines = [r"\begin{figure}[htbp]", r"\centering", r"\includegraphics[width=\linewidth]{figure.pdf}"]
        if caption:
            lines.append(r"\caption{" + tex_text(caption) + "}")
        if label:
            lines.append(r"\label{" + label + "}")
        lines.append(r"\end{figure}")
        (package / "figure.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
        manifest = {"caption": caption, "label": label, "provenance": provenance, "checks": checks,
                    "files": {path.relative_to(package).as_posix(): digest(path)
                              for path in sorted(package.rglob("*")) if path.is_file()}}
        (package / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # rename refuses a concurrently populated target directory.
        package.rename(output)
    return {"output": str(output), **manifest}
