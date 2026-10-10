"""Independent tools for engineering papers."""

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import zipfile

from .files import pack_files, read_json, write_json
from . import __version__


def parser():
    root = argparse.ArgumentParser(prog="thesis", description="工程论文工具集")
    root.add_argument("--version", action="version", version="thesis " + __version__)
    commands = root.add_subparsers(dest="command", required=True)
    item = commands.add_parser("compare", help="本地比对稿件与指定参考资料的相似句段")
    item.add_argument("source", type=Path)
    item.add_argument("references", type=Path, nargs="+")
    item.add_argument("--output", type=Path, required=True)
    item.add_argument("--threshold", type=float, default=85)
    item.add_argument("--min-chars", type=int, default=20)
    item = commands.add_parser("import-doc", help="飞书 XML 或导出 JSON 转 TeX")
    item.add_argument("source", type=Path)
    item.add_argument("output", type=Path)
    item.add_argument("--assets", type=Path)
    item.add_argument("--source-url", default="")
    item = commands.add_parser("excerpt", help="摘录代码和版本来源")
    item.add_argument("repo", type=Path)
    item.add_argument("file")
    item.add_argument("output", type=Path)
    item.add_argument("--start", type=int, default=1)
    item.add_argument("--end", type=int)
    item.add_argument("--revision")
    item.add_argument("--caption", default="")
    item.add_argument("--label", default="")
    item = commands.add_parser("figure", help="打包图源、SVG 和 PDF")
    item.add_argument("output", type=Path)
    item.add_argument("--source", type=Path, required=True)
    item.add_argument("--svg", type=Path, required=True)
    item.add_argument("--pdf", type=Path, required=True)
    item.add_argument("--caption", default="")
    item.add_argument("--label", default="")
    item.add_argument("--provenance", default="")
    item = commands.add_parser("plot", help="CSV 绘制矢量数据图，保留可运行图源")
    item.add_argument("data", type=Path)
    item.add_argument("output", type=Path)
    item.add_argument("--kind", choices=("line", "bar", "scatter", "box", "hist"), default="line")
    item.add_argument("--x")
    item.add_argument("--y", nargs="+")
    for name in ("title", "xlabel", "ylabel", "caption", "label"):
        item.add_argument("--" + name, default="")
    item.add_argument("--font")
    item = commands.add_parser("table", help="CSV 转三线表或横向跨页表")
    item.add_argument("source", type=Path)
    item.add_argument("output", type=Path)
    item.add_argument("--caption", default="")
    item.add_argument("--label", default="")
    item.add_argument("--landscape", action="store_true")
    item = commands.add_parser("import-template", help="导入 NJUThesis 源 ZIP")
    item.add_argument("archive", type=Path)
    item.add_argument("output", type=Path)
    item.add_argument("--main", default="njuthesis-sample.tex")
    item.add_argument("--type", choices=("bachelor", "master", "doctor", "postdoc"))
    item.add_argument("--degree", choices=("academic", "professional"))
    for name, description in (("inspect-template", "检查导入模板"), ("assemble", "将章节填入模板副本")):
        item = commands.add_parser(name, help=description)
        item.add_argument("project", type=Path)
    item = commands.add_parser("check", help="检查 TeX 引用、标签和文件依赖")
    item.add_argument("source", type=Path)
    item.add_argument("--bib", type=Path, action="append")
    item = commands.add_parser("build", help="编译指定 TeX 主文件")
    item.add_argument("main", type=Path)
    item.add_argument("output", type=Path)
    item.add_argument("--timeout", type=int, default=180)
    item.add_argument("--skip-preview", action="store_true", help="仅编译与结构检查，明确跳过 PDF.js")
    item.add_argument("--pdfjs-modules", type=Path)
    item.add_argument("--cmap", type=Path, help="用 Adobe-GB1-UCS2 为适用字体生成修复副本")
    item.add_argument("--bibliography-source", help="本地 .bib 或 Better BibTeX 本机导出 URL")
    item.add_argument("--bibliography-target", default="references.bib", help="编译副本内的文献相对路径")
    for name, description in (("check-log", "检查 TeX 编译日志"), ("inspect-pdf", "检查 PDF 结构、页数和图片对象")):
        item = commands.add_parser(name, help=description)
        item.add_argument("source", type=Path)
        if name == "inspect-pdf":
            item.add_argument("--preview-dir", type=Path, help="运行 PDF.js 对照并保存逐页 PNG")
            item.add_argument("--pdfjs-modules", type=Path)
            item.add_argument("--pages", help="预览页码，如 1,3-5；默认全部")
            item.add_argument("--expect-text", action="append", default=[])
            item.add_argument("--repair-to", type=Path)
            item.add_argument("--cmap", type=Path)
            item.add_argument("--timeout", type=int, default=180)
    item = commands.add_parser("literature-search", help="OpenAlex 文献搜索与引用关系展开")
    item.add_argument("query", nargs="?", default="")
    item.add_argument("--output", type=Path, required=True)
    item.add_argument("--limit", type=int, default=10)
    item.add_argument("--year")
    mode = item.add_mutually_exclusive_group()
    mode.add_argument("--cites", help="列出引用指定 DOI 或 OpenAlex ID 的论文")
    mode.add_argument("--references", help="展开指定论文引用的文献")
    item.add_argument("--timeout", type=int, default=30)
    item = commands.add_parser("reference-check", help="Crossref 核对 DOI 或 .bib 书目信息")
    item.add_argument("source")
    item.add_argument("--output", type=Path, required=True)
    item.add_argument("--timeout", type=int, default=30)
    item = commands.add_parser("bibliography", help="同步本地或 Zotero BibLaTeX，保留引用键")
    item.add_argument("source")
    item.add_argument("output", type=Path)
    item.add_argument("--existing", type=Path, help="核对已有文献的引用键未发生变化")
    item.add_argument("--timeout", type=int, default=30)
    item = commands.add_parser("read-paper", help="Docling 本地解析，保留原件、页码与框坐标")
    item.add_argument("source", type=Path)
    item.add_argument("output", type=Path)
    item.add_argument("--docling", type=Path)
    item.add_argument("--pages", help="原文页码，例如 1-4")
    item.add_argument("--no-ocr", action="store_true")
    item.add_argument("--pipeline", choices=("standard", "native"), default="standard")
    item.add_argument("--timeout", type=int, default=600)
    item = commands.add_parser("pack", help="归档指定文件和目录，附 SHA-256 清单")
    item.add_argument("output", type=Path)
    item.add_argument("sources", type=Path, nargs="+")
    commands.add_parser("doctor", help="查看本机依赖")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "compare":
            from .similarity import compare_passages
            result = compare_passages(args.source, args.references, args.output, args.threshold, args.min_chars)
        elif args.command == "import-doc":
            from .documents import import_document
            result = import_document(args.source, args.output, args.assets, args.source_url)
        elif args.command == "table":
            from .documents import csv_table
            result = csv_table(args.source, args.output, args.caption, args.label, args.landscape)
        elif args.command == "excerpt":
            from .excerpts import export_excerpt
            result = export_excerpt(args.repo, args.file, args.output, args.start, args.end,
                                    args.revision, args.caption, args.label)
        elif args.command == "figure":
            from .figures import package_figure
            result = package_figure(args.output, args.source, args.svg, args.pdf,
                                    args.caption, args.label, args.provenance)
        elif args.command == "plot":
            from .plots import create_plot
            result = create_plot(args.data, args.output, args.kind, args.x, args.y, args.title,
                                 args.xlabel, args.ylabel, args.caption, args.label, args.font)
        elif args.command == "import-template":
            from .texproject import import_project
            if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
                raise ValueError("模板输出目录必须不存在或为空")
            manuscript = import_project(args.output, args.archive, args.main)
            for key, value in (("type", args.type), ("degree", args.degree)):
                if value:
                    manuscript[key] = value
            write_json(args.output, "thesis.json", {"manuscript": manuscript}, overwrite=False)
            result = {"output": str(args.output.resolve()), "manuscript": manuscript}
        elif args.command in ("inspect-template", "assemble"):
            from .texproject import assemble_project, inspect_project
            config = read_json(args.project, "thesis.json")
            result = (assemble_project if args.command == "assemble" else inspect_project)(args.project, config)
            if args.command == "inspect-template":
                result["ok"] = not result["missing_inputs"]
        elif args.command == "check":
            from .checks import check_tex
            result = check_tex(args.source, args.bib)
        elif args.command == "build":
            from .texbuild import build_tex
            result = build_tex(args.main, args.output, args.timeout, args.skip_preview, args.pdfjs_modules,
                               args.cmap, args.bibliography_source, args.bibliography_target)
        elif args.command == "check-log":
            from .texbuild import check_compile_log
            findings = check_compile_log(args.source)
            result = {"ok": not findings, "findings": findings}
        elif args.command == "inspect-pdf":
            from .checks import inspect_pdf
            if (args.pages or args.expect_text) and not args.preview_dir:
                raise ValueError("--pages 和 --expect-text 需要 --preview-dir 才会执行实际渲染")
            repair = None
            source = args.source
            if args.repair_to:
                if not args.cmap or not args.preview_dir:
                    raise ValueError("修复需同时指定 --cmap 和 --preview-dir，确保修复后实际渲染")
                from .pdfpreview import repair_cmap
                repair = repair_cmap(source, args.repair_to, args.cmap)
                source = args.repair_to
            elif args.cmap:
                raise ValueError("--cmap 需要同时使用 --repair-to")
            result = inspect_pdf(source, args.preview_dir, args.pdfjs_modules, args.pages, args.expect_text, args.timeout)
            if repair:
                result["repair"] = repair
        elif args.command == "literature-search":
            from .literature import search_literature
            result = search_literature(args.query, args.output, args.limit, args.year, args.cites, args.references, args.timeout)
        elif args.command == "reference-check":
            from .literature import check_references
            result = check_references(args.source, args.output, args.timeout)
        elif args.command == "bibliography":
            from .bibliography import sync_bibliography
            result = sync_bibliography(args.source, args.output, args.existing, args.timeout)
        elif args.command == "read-paper":
            from .papers import read_paper
            result = read_paper(args.source, args.output, args.docling, args.pages, not args.no_ocr, args.pipeline, args.timeout)
        elif args.command == "pack":
            result = pack_files(args.sources, args.output)
        else:
            from .external import pdfjs_modules, tool_path
            result = {"commands": {name: shutil.which(name) for name in
                                  ("latexmk", "xelatex", "biber", "lark-cli", "njucli", "node")},
                      "matplotlib": importlib.util.find_spec("matplotlib") is not None,
                      "rapidfuzz": importlib.util.find_spec("rapidfuzz") is not None,
                      "pybtex": importlib.util.find_spec("pybtex") is not None,
                      "docling": tool_path("docling"),
                      "pdfjs_modules": str(pdfjs_modules()) if pdfjs_modules() else None}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", True) else 2
    except (ValueError, OSError, RuntimeError, zipfile.BadZipFile) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1
