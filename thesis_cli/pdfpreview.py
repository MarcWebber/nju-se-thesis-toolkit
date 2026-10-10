"""Audit CJK font mapping and compare local PDF.js rendering."""

import json
from pathlib import Path
import shutil
import subprocess

from .external import fresh_directory, pdfjs_modules, run_logged
from .files import digest, write_json


def font_records(reader):
    fonts, visited = {}, set()

    def visit(resources, page_no):
        resources = resources.get_object()
        for ref in resources.get("/Font", {}).get_object().values() if "/Font" in resources else []:
            font = ref.get_object()
            key = (getattr(ref, "idnum", id(font)), getattr(ref, "generation", 0))
            if key not in fonts:
                desc = font.get("/DescendantFonts", [])
                child = desc[0].get_object() if desc else font
                info = child["/CIDSystemInfo"].get_object() if "/CIDSystemInfo" in child else {}
                descriptor = child.get("/FontDescriptor", {})
                descriptor = descriptor.get_object() if descriptor else {}
                ordering = str(info.get("/Ordering", ""))
                encoding = str(font.get("/Encoding", ""))
                risk = (ordering in {"GB1", "CNS1", "Japan1", "Korea1"} and
                        encoding in {"/Identity-H", "/Identity-V"} and "/ToUnicode" not in font)
                fonts[key] = {"name": str(font.get("/BaseFont", "")), "encoding": encoding,
                              "registry": str(info.get("/Registry", "")), "ordering": ordering,
                              "embedded": any(k in descriptor for k in ("/FontFile", "/FontFile2", "/FontFile3")),
                              "to_unicode": "/ToUnicode" in font, "external_cmap_risk": risk, "pages": [], "object": font}
            if page_no not in fonts[key]["pages"]:
                fonts[key]["pages"].append(page_no)
        for ref in resources.get("/XObject", {}).get_object().values() if "/XObject" in resources else []:
            obj = ref.get_object()
            identity = (id(obj), page_no)
            if identity not in visited and obj.get("/Subtype") == "/Form" and "/Resources" in obj:
                visited.add(identity)
                visit(obj["/Resources"], page_no)

    for number, page in enumerate(reader.pages, 1):
        if "/Resources" in page:
            visit(page["/Resources"], number)
    return list(fonts.values())


def repair_cmap(source, target, mapping):
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject
    source, target, mapping = Path(source).resolve(), Path(target).absolute(), Path(mapping).resolve()
    if target.exists() or target.is_symlink() or source == target.resolve():
        raise ValueError("修复输出必须是新文件，不能覆盖原 PDF")
    data = mapping.read_bytes()
    if b"/CMapName /Adobe-GB1-UCS2" not in data:
        raise ValueError("仅接受 Adobe-GB1-UCS2 映射；其他 CID 字体不自动修复")
    writer = PdfWriter()
    writer.clone_document_from_reader(PdfReader(source, strict=True))
    fonts = font_records(writer)
    candidates = [f for f in fonts if f["external_cmap_risk"] and f["registry"] == "Adobe" and
                  f["ordering"] == "GB1" and f["encoding"] == "/Identity-H"]
    if not candidates:
        raise ValueError("没有可用此 Adobe GB1 映射修复的字体；未生成副本")
    stream = DecodedStreamObject()
    stream.set_data(data)
    ref = writer._add_object(stream.flate_encode())
    for font in candidates:
        font["object"][NameObject("/ToUnicode")] = ref
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as handle:
        writer.write(handle)
    return {"source": str(source), "source_sha256": digest(source), "output": str(target.resolve()),
            "output_sha256": digest(target), "mapping": str(mapping), "mapping_sha256": digest(mapping),
            "fonts": [f["name"] for f in candidates]}


def render_pdf(path, output, modules=None, pages=None, expected=None, timeout=180):
    modules = pdfjs_modules(modules)
    if not modules or not (modules / "pdfjs-dist/package.json").is_file() or not (modules / "@napi-rs/canvas/package.json").is_file():
        raise RuntimeError("缺少 PDF.js 预览依赖；按 docs/integrations.md 安装或设置 THESIS_PDFJS_MODULES")
    node = shutil.which("node")
    if not node:
        raise RuntimeError("PDF.js 检查需要 Node.js")
    output = fresh_directory(output)
    config = {"source": str(Path(path).resolve()), "output": str(output), "modules": str(modules),
              "pages": pages, "expected": expected or []}
    write_json(output, "request.json", config)
    run_logged([node, str(Path(__file__).with_name("pdfpreview.mjs")), str(output / "request.json")],
               output / "render.log", timeout)
    result = json.loads((output / "preview.json").read_text(encoding="utf-8"))
    result["directory"] = str(output)
    return result
